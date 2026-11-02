"""Chấm điểm thang đo theo thư viện scales/*.yaml.

Nguyên tắc:
- Không tự sửa dữ liệu: phát hiện mã hóa lệch thì dừng lại chờ học sinh xác nhận 'dich_chuyen'.
- Giá trị ngoài khoảng thì không tính điểm, trả danh sách dòng lỗi để học sinh sửa.
- Thiếu câu nào trong một tiểu thang/thang thì không tính điểm đó cho người này (mặc định hệ thống).
- Chỉ trả kết quả theo nhóm; điểm từng người chỉ dùng nội bộ cho các phân tích tiếp theo.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .descriptives import summary_numeric
from .utils import LoiPhanTich, require_column, to_numeric

NHOM_TOI_THIEU_PHAN_BO = 5
SO_DONG_LOI_TOI_DA = 20


def load_library(folder: Path) -> dict:
    lib = {}
    for f in sorted(Path(folder).glob("*.yaml")):
        spec = yaml.safe_load(f.read_text(encoding="utf-8"))
        lib[spec["ma"]] = spec
    return lib


# ---------- Chuẩn hóa yêu cầu thành kế hoạch tính điểm theo tên cột ----------

def build_plan(spec: dict, req: dict) -> dict:
    gv = req.get("gia_tri") or spec.get("gia_tri") or {}
    if "min" not in gv or "max" not in gv:
        raise LoiPhanTich("Cần khai báo khoảng giá trị (min, max) của thang.")
    lo, hi = gv["min"], gv["max"]

    if spec["ma"] == "LIKERT":
        bien = req.get("bien") or []
        if not bien:
            raise LoiPhanTich("Thang tự xây dựng cần danh sách 'bien' (mỗi biến gồm mã, các cột, các cột đảo).")
        subs, items, reverse = [], [], set()
        for b in bien:
            cols = b.get("cot") or []
            if len(cols) < 1:
                raise LoiPhanTich(f"Biến '{b.get('ma')}' chưa có cột nào.")
            dao = set(b.get("dao") or [])
            if not dao <= set(cols):
                raise LoiPhanTich(f"Cột đảo của biến '{b.get('ma')}' phải nằm trong danh sách cột của biến đó.")
            subs.append({"ma": b["ma"], "ten": b.get("ten", b["ma"]), "cols": cols,
                         "cach_tinh": "trung_binh", "he_so": 1})
            items += [c for c in cols if c not in items]
            reverse |= dao
        return {"lo": lo, "hi": hi, "items": items, "reverse": reverse, "subs": subs,
                "total": {"cach_tinh": "khong_co"}, "prefix": None, "special": None}

    cot = req.get("cot") or []
    n = spec.get("so_cau")
    if len(cot) != n:
        raise LoiPhanTich(f"Thang {spec['ma']} có {n} câu nhưng mới chọn {len(cot)} cột. "
                          "Hãy chọn đủ cột theo đúng thứ tự câu 1, 2, 3…")
    if len(set(cot)) != len(cot):
        raise LoiPhanTich("Một cột bị chọn cho nhiều câu.")

    def c(i):
        return cot[i - 1]

    subs = [{"ma": s["ma"], "ten": s.get("ten", s["ma"]), "cols": [c(i) for i in s["cau"]],
             "cach_tinh": s.get("cach_tinh", "trung_binh"), "he_so": s.get("he_so", 1)}
            for s in (spec.get("tieu_thang") or [])]
    special = spec.get("canh_bao_rieng")
    return {"lo": lo, "hi": hi, "items": list(cot), "reverse": {c(i) for i in spec.get("cau_dao_nguoc") or []},
            "subs": subs, "total": spec.get("diem_tong") or {"cach_tinh": "khong_co"},
            "prefix": spec["ma"], "special": ({"cau": special["cau"], "cot": c(special["cau"])} if special else None)}


# ---------- Kiểm tra dữ liệu ----------

def _excel_rows(index) -> list:
    """Số dòng như trong Excel (dòng 1 là tiêu đề)."""
    return [int(i) + 2 for i in list(index)[:SO_DONG_LOI_TOI_DA]]


def check_items(raw: pd.DataFrame, num: pd.DataFrame, lo, hi) -> dict:
    khong_phai_so, ngoai_khoang, khong_nguyen = {}, {}, {}
    for col in num.columns:
        bad_text = raw[col].notna() & num[col].isna()
        if bad_text.any():
            khong_phai_so[col] = _excel_rows(raw.index[bad_text])
        v = num[col]
        out = v.notna() & ((v < lo) | (v > hi))
        if out.any():
            ngoai_khoang[col] = _excel_rows(v.index[out])
        frac = v.notna() & (v != v.round())
        if frac.any():
            khong_nguyen[col] = _excel_rows(v.index[frac])
    return {"khong_phai_so": khong_phai_so, "ngoai_khoang": ngoai_khoang, "khong_nguyen": khong_nguyen}


def detect_offset(num: pd.DataFrame, lo, hi) -> dict | None:
    """Toàn bộ dữ liệu lệch đều 1 đơn vị so với khoảng của thang (ví dụ 1–4 thay vì 0–3)."""
    vals = num.stack()
    if vals.empty or (vals.min() >= lo and vals.max() <= hi):
        return None
    for d in (1, -1):
        if vals.min() >= lo + d and vals.max() <= hi + d:
            return {"phat_hien": True, "goi_y_tru": d, "khoang_quan_sat": [vals.min(), vals.max()],
                    "khoang_cua_thang": [lo, hi]}
    return None


def cronbach_alpha(items: pd.DataFrame):
    x = items.dropna()
    k = x.shape[1]
    if k < 2 or len(x) < 2:
        return None
    total_var = x.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return None
    return k / (k - 1) * (1 - x.var(ddof=1).sum() / total_var)


def corrected_item_total(items: pd.DataFrame) -> dict:
    x = items.dropna()
    out = {}
    if x.shape[1] < 3 or len(x) < 3:
        return out
    for col in x.columns:
        rest = x.drop(columns=col).sum(axis=1)
        if x[col].std() > 0 and rest.std() > 0:
            out[col] = float(np.corrcoef(x[col], rest)[0, 1])
    return out


def item_total_statistics(items: pd.DataFrame) -> list[dict]:
    """Bảng Item-Total Statistics như SPSS: tính trên người trả lời đủ mọi câu, sau khi đảo câu ngược.
    Mỗi câu: trung bình và phương sai của tổng các câu còn lại, tương quan biến–tổng hiệu chỉnh, α nếu loại câu."""
    x = items.dropna()
    if x.shape[1] < 3 or len(x) < 3:
        return []
    itc = corrected_item_total(x)
    out = []
    for col in x.columns:
        rest = x.drop(columns=col)
        total = rest.sum(axis=1)
        out.append({"cot": col, "mean_neu_loai": float(total.mean()), "var_neu_loai": float(total.var(ddof=1)),
                    "tuong_quan_bien_tong": itc.get(col), "alpha_neu_loai": cronbach_alpha(rest)})
    return out


def mapping_table(df: pd.DataFrame, spec: dict, req: dict) -> list[dict]:
    """Bảng ghép câu – cột để học sinh soát trước khi tính điểm.
    'nghi_sai_vi_tri': sau khi đảo đúng các câu đảo chiều, câu này vẫn tương quan âm với phần còn lại của
    tiểu thang – dấu hiệu cột bị đặt sai vị trí câu hoặc câu đảo chiều khai báo sai."""
    plan = build_plan(spec, req)
    sub_of = {c: s["ma"] for s in plan["subs"] for c in s["cols"]}
    present = [c for c in plan["items"] if c in df.columns]
    num = df[present].apply(to_numeric)
    items = num.copy()
    for c in plan["reverse"] & set(present):
        items[c] = plan["lo"] + plan["hi"] - items[c]
    itc = {}
    blocks = [s["cols"] for s in plan["subs"]] or [plan["items"]]
    for cols in blocks:
        itc.update(corrected_item_total(items[[c for c in cols if c in present]]))
    rows = []
    for i, c in enumerate(plan["items"], 1):
        v = num[c] if c in present else pd.Series(dtype=float)
        rows.append({"cau": i, "cot": c, "co_trong_file": c in present, "tieu_thang": sub_of.get(c),
                     "dao_chieu": c in plan["reverse"], "min": v.min(), "max": v.max(), "n": int(v.notna().sum()),
                     "tuong_quan_bien_tong": itc.get(c), "nghi_sai_vi_tri": itc.get(c) is not None and itc[c] < 0})
    return rows


# ---------- Tính điểm ----------

def _aggregate(block: pd.DataFrame, cach_tinh: str, he_so: float) -> pd.Series:
    complete = block.notna().all(axis=1)
    if cach_tinh == "tong":
        s = block.sum(axis=1)
    elif cach_tinh == "trung_binh":
        s = block.mean(axis=1)
    else:
        raise LoiPhanTich(f"Cách tính '{cach_tinh}' không hợp lệ.")
    return (s * he_so).where(complete)


def bands_for(spec: dict, code: str, lo, hi):
    if spec["ma"] == "LIKERT":
        if lo == 1 and hi == 5:
            return spec.get("phan_loai_5_muc")
        if lo == 1 and hi == 7:
            return spec.get("phan_loai_7_muc")
        return None
    pl = spec.get("phan_loai")
    if isinstance(pl, dict):
        return pl.get(code)
    if isinstance(pl, list) and pl and code == "TONG":
        return pl
    return None


def classify(value, bands):
    """Chọn mức có 'tu' lớn nhất mà vẫn ≤ giá trị (xử lý được khoảng trống như 1,80 → 1,81)."""
    if value is None or pd.isna(value):
        return None
    chosen = None
    for b in sorted(bands, key=lambda b: b["tu"]):
        if value >= b["tu"] - 1e-9:
            chosen = b["muc"]
    return chosen


def score(df: pd.DataFrame, spec: dict, req: dict) -> tuple[pd.DataFrame, dict]:
    """Trả về (bảng điểm theo từng người – chỉ dùng nội bộ, báo cáo theo nhóm cho AI)."""
    plan = build_plan(spec, req)
    lo, hi = plan["lo"], plan["hi"]
    for col in plan["items"]:
        require_column(df, col)
    raw = df[plan["items"]]
    num = raw.apply(to_numeric)

    report = {"analysis": "thang-do", "scale": _scale_summary(spec, plan), "trang_thai": "ok",
              "bang_ghep": mapping_table(df, spec, req)}
    shift = req.get("dich_chuyen")
    if shift is None:
        lech = detect_offset(num, lo, hi)
        if lech:
            report.update(trang_thai="can_xac_nhan", kiem_tra={"lech_ma_hoa": lech},
                          thong_bao=(f"Dữ liệu nằm trong khoảng {lech['khoang_quan_sat']} nhưng thang gốc là "
                                     f"[{lo}, {hi}]. Nếu phiếu đã mã hóa lệch, hãy xác nhận để trừ "
                                     f"{lech['goi_y_tru']} cho mọi câu."))
            return pd.DataFrame(index=df.index), report
    else:
        num = num - float(shift)

    checks = check_items(raw, num, lo, hi)
    if any(checks.values()):
        report.update(trang_thai="loi_du_lieu", kiem_tra=checks,
                      thong_bao="Có giá trị không hợp lệ (số dòng tính như Excel). Sửa dữ liệu rồi chạy lại.")
        return pd.DataFrame(index=df.index), report

    special = None
    if plan["special"]:
        k = int((num[plan["special"]["cot"]] > 0).sum())
        if k > 0:
            special = {"cau": plan["special"]["cau"], "so_nguoi_tra_loi_lon_hon_0": k,
                       "noi_dung": spec["canh_bao_rieng"]["noi_dung"]}

    # Đảo chiều: giá trị mới = min + max − giá trị cũ
    items = num.copy()
    for col in plan["reverse"]:
        items[col] = lo + hi - items[col]

    scores = pd.DataFrame(index=df.index)
    meta = {}
    for s in plan["subs"]:
        name = f"{plan['prefix']}_{s['ma']}" if plan["prefix"] else s["ma"]
        scores[name] = _aggregate(items[s["cols"]], s["cach_tinh"], s["he_so"])
        meta[s["ma"]] = {"cot_diem": name, "ten": s["ten"], "cols": s["cols"]}

    total = plan["total"]
    ct = total.get("cach_tinh", "khong_co")
    if ct != "khong_co":
        tname = f"{plan['prefix']}_TONG"
        if ct == "trung_binh_cac_tieu_thang":
            sub_cols = [m["cot_diem"] for m in meta.values()]
            block = scores[sub_cols]
            scores[tname] = block.mean(axis=1).where(block.notna().all(axis=1)) * total.get("he_so", 1)
        else:
            scores[tname] = _aggregate(items[plan["items"]], ct, total.get("he_so", 1))
        meta["TONG"] = {"cot_diem": tname, "ten": "Điểm tổng", "cols": plan["items"]}

    ket_qua, n_loai, alpha, itc_am, tuong_quan_2_cau, thong_ke_cau = {}, {}, {}, {}, {}, {}
    for code, m in meta.items():
        col = m["cot_diem"]
        sc = scores[col]
        desc = summary_numeric(sc)
        n_loai[code] = int(sc.isna().sum())
        entry = {"ten": m["ten"], "cot_diem": col, "n": desc["n_valid"], "mean": desc["mean"], "sd": desc["sd"],
                 "median": desc["median"], "min": desc["min"], "max": desc["max"], "skewness": desc["skewness"]}
        bands = bands_for(spec, code, lo, hi)
        if bands and desc["n_valid"] >= NHOM_TOI_THIEU_PHAN_BO:
            levels = sc.dropna().map(lambda v: classify(v, bands))
            entry["phan_bo_muc"] = {b["muc"]: float((levels == b["muc"]).mean() * 100)
                                   for b in sorted(bands, key=lambda b: b["tu"])}
        ket_qua[code] = entry
        block = items[m["cols"]]
        if len(m["cols"]) >= 3:
            alpha[code] = cronbach_alpha(block)
            thong_ke_cau[code] = item_total_statistics(block)
            neg = {c: r for c, r in corrected_item_total(block).items() if r < 0}
            if neg:
                itc_am[code] = neg
        elif len(m["cols"]) == 2:
            x = block.dropna()
            if len(x) > 2 and x.iloc[:, 0].std() > 0 and x.iloc[:, 1].std() > 0:
                tuong_quan_2_cau[code] = float(np.corrcoef(x.iloc[:, 0], x.iloc[:, 1])[0, 1])

    report.update(
        kiem_tra={"ngoai_khoang": {}, "lech_ma_hoa": False, "dich_chuyen_da_ap_dung": shift,
                  "tuong_quan_bien_tong_am": itc_am, "n_bi_loai_do_thieu": n_loai,
                  "cronbach": alpha, "tuong_quan_2_cau": tuong_quan_2_cau, "thong_ke_cau": thong_ke_cau},
        ket_qua=ket_qua, canh_bao_rieng=special)
    return scores, report


def _scale_summary(spec: dict, plan: dict) -> dict:
    keep = ("ma", "ten_viet", "tac_gia", "gia_tri", "cau_dao_nguoc", "diem_tong", "loai_nguong",
            "nguon_phan_loai", "nhay_cam", "canh_bao", "ban_tieng_viet")
    out = {k: spec.get(k) for k in keep}
    out["gia_tri"] = {"min": plan["lo"], "max": plan["hi"]}
    out["tieu_thang"] = [{"ma": s["ma"], "ten": s["ten"], "cach_tinh": s["cach_tinh"], "he_so": s["he_so"]}
                         for s in plan["subs"]]
    if spec["ma"] == "LIKERT":
        out["cot_dao"] = sorted(plan["reverse"])
    return out


HAU_TO_LIKERT = "_TB"
HAU_TO_THANG = "_DIEM"


def score_column_name(name: str, is_likert: bool, existing) -> str:
    """Tên cột điểm do web tính. Trùng với cột có sẵn trong file (thường là cột học sinh tự tính trong Excel)
    thì thêm hậu tố. Giao diện dùng đúng quy tắc này để biết tên biến."""
    return name + (HAU_TO_LIKERT if is_likert else HAU_TO_THANG) if name in existing else name


def _compare_with_existing(web: pd.Series, own: pd.Series) -> dict:
    """So điểm web tính với cột cùng tên học sinh tự tính."""
    own = to_numeric(own)
    both = web.notna() & own.notna()
    if not both.any():
        return {"so_sanh_duoc": False}
    diff = (web[both] - own[both]).abs()
    return {"so_sanh_duoc": True, "n": int(both.sum()), "khop": bool((diff < 0.01).all()),
            "so_dong_lech": int((diff >= 0.01).sum()), "lech_lon_nhat": float(diff.max())}


def apply_all(df: pd.DataFrame, library: dict, requests: list) -> tuple[pd.DataFrame, list]:
    """Chấm điểm mọi thang được khai báo; thêm cột điểm vào bảng để dùng cho t-test/ANOVA."""
    reports = []
    out = df.copy()
    for req in requests or []:
        ma = req.get("ma")
        if ma not in library:
            raise LoiPhanTich(f"Thang '{ma}' chưa có trong thư viện. Cần lấy cách tính từ bài báo gốc "
                              "và nhờ giáo viên bổ sung vào thư viện.")
        scores, rep = score(out, library[ma], req)
        renamed = {}
        for col in scores.columns:
            new = score_column_name(col, ma == "LIKERT", out.columns)
            if new in out.columns:
                raise LoiPhanTich(f"File đã có cả cột '{col}' và '{new}'. Hãy đổi tên một trong hai cột rồi tải lại.")
            if new != col:
                renamed[col] = {"cot_moi": new, **_compare_with_existing(scores[col], out[col])}
        if renamed:
            scores = scores.rename(columns={c: v["cot_moi"] for c, v in renamed.items()})
            for kq in (rep.get("ket_qua") or {}).values():
                if kq["cot_diem"] in renamed:
                    kq["cot_diem"] = renamed[kq["cot_diem"]]["cot_moi"]
            rep["doi_ten_cot_diem"] = renamed
        out = pd.concat([out, scores], axis=1)
        reports.append(rep)
    return out, reports


def rename_warnings(reports: list) -> list[str]:
    """Thông báo cho học sinh khi cột điểm phải đổi tên vì trùng cột có sẵn trong file."""
    out = []
    for rep in reports:
        for old, info in (rep.get("doi_ten_cot_diem") or {}).items():
            msg = (f"File đã có cột **{old}** (có thể bạn đã tự tính trong Excel). Điểm do web tính được đặt tên "
                   f"**{info['cot_moi']}**.")
            if info.get("so_sanh_duoc"):
                if info["khop"]:
                    msg += f" Hai cột khớp nhau ở cả {info['n']} người: cách bạn tự tính là đúng."
                else:
                    msg += (f" Hai cột lệch nhau ở {info['so_dong_lech']}/{info['n']} người. Hãy kiểm tra lại cách "
                            "tính trong Excel, đặc biệt là các câu đảo chiều; nên dùng điểm do web tính.")
            out.append(msg)
    return out
