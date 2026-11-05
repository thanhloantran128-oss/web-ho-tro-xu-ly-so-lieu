"""Câu hỏi nghiên cứu → giả thuyết → phép phân tích → cỡ mẫu (kế hoạch nghiên cứu cho học sinh THPT).

Không dùng AI: dạng câu hỏi và loại biến quyết định phép phân tích theo quy tắc cố định, nên cùng một kế hoạch luôn
cho cùng một kết quả. Lời văn nằm trong giai-thich/cau-hoi.yaml.

Kế hoạch (JSON):
{
  "ten_de_tai": "…", "doi_tuong": "học sinh khối 10–12",
  "bien": [
    {"ma": "GioiTinh", "ten": "Giới tính", "kieu": "phan_loai", "nhom": ["Nam", "Nữ"]},
    {"ma": "GioNgu", "ten": "Số giờ ngủ", "kieu": "dinh_luong", "min": 0, "max": 24},
    {"ma": "HT", "ten": "Hứng thú học tập", "kieu": "likert", "so_cau": 5, "so_muc": 5},
    {"ma": "CangThang", "ten": "Mức căng thẳng", "kieu": "thang_chuan", "thang": "PSS-10"},
    {"ma": "Kenh", "ten": "Kênh thông tin", "kieu": "nhieu_lua_chon", "nhom": ["Facebook", "TikTok"]}
  ],
  "cau_hoi": [{"dang": "so_sanh", "x": "GioiTinh", "y": "CangThang", "cau_hoi_rieng": "…tùy chọn…"}]
}
Dạng: mo_ta (chỉ x) · so_sanh (x = biến nhóm, y = biến cần so sánh) · lien_he (x, y) · truoc_sau (x = lần 1, y = lần 2).
"""
import math
import re
import unicodedata
from io import BytesIO
from pathlib import Path

import yaml
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from scipy import stats

from .template import BORDER, FONT, HEADER_FILL, TEN_HOP_LE
from .utils import LoiPhanTich

T = yaml.safe_load((Path(__file__).resolve().parents[2] / "giai-thich" / "cau-hoi.yaml").read_text(encoding="utf-8"))
KIEU = set(T["kieu_bien"])
SO = {"dinh_luong", "likert", "thang_chuan"}          # biến cho phép tính trung bình
DANG = set(T["dang"])
SO_BIEN_TOI_DA, SO_CAU_TOI_DA = 40, 20
ALPHA, POWER = 0.05, 0.80


# ---------- Cỡ mẫu (hai phía, α = ,05, power = ,80; mức ảnh hưởng theo Cohen, 1988) ----------
# Căn cứ, công thức và tài liệu tham khảo nằm trong giai-thich/cau-hoi.yaml (mục co_mau).

def n_ttest_doc_lap(d: float = 0.5) -> int:
    """Số người mỗi nhóm."""
    for n in range(2, 5000):
        df = 2 * n - 2
        nc = d * math.sqrt(n / 2)
        crit = stats.t.ppf(1 - ALPHA / 2, df)
        if stats.nct.sf(crit, df, nc) + stats.nct.cdf(-crit, df, nc) >= POWER:
            return n
    return 5000


def n_ttest_cap(d: float = 0.5) -> int:
    for n in range(2, 5000):
        df = n - 1
        nc = d * math.sqrt(n)
        crit = stats.t.ppf(1 - ALPHA / 2, df)
        if stats.nct.sf(crit, df, nc) + stats.nct.cdf(-crit, df, nc) >= POWER:
            return n
    return 5000


def n_anova(k: int, f: float = 0.25) -> int:
    """Số người mỗi nhóm (các nhóm bằng nhau)."""
    for n in range(2, 5000):
        total = n * k
        crit = stats.f.ppf(1 - ALPHA, k - 1, total - k)
        if stats.ncf.sf(crit, k - 1, total - k, f ** 2 * total) >= POWER:
            return n
    return 5000


def n_chi2(df: int, w: float = 0.3) -> int:
    crit = stats.chi2.ppf(1 - ALPHA, df)
    for n in range(5, 20000):
        if stats.ncx2.sf(crit, df, w ** 2 * n) >= POWER:
            return n
    return 20000


def n_tuong_quan(r: float = 0.3) -> int:
    z = stats.norm.ppf(1 - ALPHA / 2) + stats.norm.ppf(POWER)
    return math.ceil((z / math.atanh(r)) ** 2 + 3)


def n_mo_ta(sai_so: float = 0.10, tong_the: int | None = None) -> int:
    """Cochran (1977): n₀ = z²·p(1−p)/e² với p = 0,5; hiệu chỉnh tổng thể hữu hạn n = n₀ / (1 + (n₀ − 1)/N)."""
    n0 = math.ceil(stats.norm.ppf(0.975) ** 2 * 0.25 / sai_so ** 2)
    return math.ceil(n0 / (1 + (n0 - 1) / tong_the)) if tong_the else n0


# ---------- Tiện ích lời văn ----------

def _giua_cau(s: str) -> str:
    """'Mức căng thẳng' → 'mức căng thẳng' khi đứng giữa câu; giữ nguyên viết tắt (GPA, MXH)."""
    s = s.strip()
    if len(s) > 1 and s[0].isupper() and not s[1].isupper():
        return s[0].lower() + s[1:]
    return s


def ma_tu_ten(ten: str) -> str:
    """'Số giờ ngủ' → 'SoGioNgu' (tên cột không dấu, dùng cho file mẫu)."""
    s = unicodedata.normalize("NFD", ten.replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    words = re.findall(r"[A-Za-z0-9]+", s)
    out = "".join(w[:1].upper() + w[1:] for w in words)
    if out and not out[0].isalpha():
        out = "B" + out
    return out[:30]


# ---------- Kiểm tra biến ----------

def _check_vars(raw: list, library: dict) -> tuple[dict, list[str]]:
    out, loi = {}, []
    for i, b in enumerate(raw[:SO_BIEN_TOI_DA], 1):
        ten = " ".join(str(b.get("ten") or "").split())
        ma = str(b.get("ma") or "").strip() or ma_tu_ten(ten)
        kieu = b.get("kieu")
        if not ten:
            loi.append(f"Biến thứ {i} chưa có tên.")
            continue
        if kieu not in KIEU:
            loi.append(f"Biến “{ten}” chưa chọn loại.")
            continue
        if not TEN_HOP_LE.match(ma):
            loi.append(f"Mã cột “{ma}” của biến “{ten}” không hợp lệ: chỉ dùng chữ không dấu, số và “_”, bắt đầu bằng chữ.")
            continue
        if kieu == "likert" and ma[-1].isdigit():
            loi.append(f"Mã “{ma}” của biến Likert “{ten}” không được kết thúc bằng số (các câu sẽ đánh số {ma}1, {ma}2…).")
            continue
        if ma.lower() in {k.lower() for k in out}:
            loi.append(f"Mã cột “{ma}” bị trùng.")
            continue
        v = {"ma": ma, "ten": ten, "kieu": kieu, "ten_kieu": T["kieu_bien"][kieu]}
        if kieu in ("phan_loai", "nhieu_lua_chon"):
            v["nhom"] = [str(x).strip() for x in b.get("nhom") or [] if str(x).strip()][:30]
        if kieu == "dinh_luong":
            for k in ("min", "max"):
                if b.get(k) not in (None, ""):
                    v[k] = float(b[k])
        if kieu == "likert":
            v["so_cau"] = max(1, min(int(b.get("so_cau") or 4), 50))
            v["so_muc"] = 7 if int(b.get("so_muc") or 5) == 7 else 5
        if kieu == "thang_chuan":
            if b.get("thang") not in library or b.get("thang") == "LIKERT":
                loi.append(f"Biến “{ten}”: hãy chọn một thang đo chuẩn trong thư viện.")
                continue
            v["thang"] = b["thang"]
            v["ten_thang"] = library[b["thang"]].get("ten_viet")
        out[ma] = v
    return out, loi


# ---------- Từng câu hỏi ----------

def _phep(code: str, analysis: str | None) -> dict:
    return {"ma": code, "ten": T["phep"][code], "phan_tich": analysis}


def _so(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def _can_cu(key: str, doi_chieu: bool) -> dict:
    C = T["co_mau"]
    B = C["can_cu"][key]
    return {"cach_tinh": B["cach_tinh"], "nguon": [C["ten_nguon"][k] for k in B["nguon"]], "nguon_ma": B["nguon"],
            "doi_chieu": B.get("doi_chieu") if doi_chieu else None}


def _co_mau(code: str, x: dict | None, y: dict | None, muc: str = "trung_binh", tong_the: int | None = None) -> dict | None:
    """Cỡ mẫu tối thiểu kèm căn cứ (cách tính, nguồn, đối chiếu với bảng của Cohen, 1992)."""
    C = T["co_mau"]
    M = C["muc"][muc]
    v = {"muc": M["ten"], **{k: _so(M[k]) for k in ("d", "f", "w", "r")}}
    tb = muc == "trung_binh"   # bảng đối chiếu chỉ ghi cho mức trung bình
    if code in ("tan-suat", "mo-ta", "trung-binh", "thang-do", "nhieu-lua-chon"):
        n = n_mo_ta(C["sai_so_mo_ta"], tong_the)
        hc = C["hieu_chinh"].format(N=tong_the) if tong_the else ""
        return {"n": n, "mo_ta": C["mo_ta"].format(n=n, hieu_chinh=hc), "can_cu": _can_cu("mo_ta", False)}
    if code == "t-test-doc-lap":
        m = n_ttest_doc_lap(M["d"])
        return {"n": 2 * m, "moi_nhom": m, "mo_ta": C["t-test-doc-lap"].format(moi_nhom=m, n=2 * m, **v),
                "can_cu": _can_cu("t-test-doc-lap", tb)}
    if code in ("anova", "so-sanh-nhom"):
        k = max(3, len((x or {}).get("nhom") or []))
        m = n_anova(k, M["f"])
        return {"n": m * k, "moi_nhom": m, "mo_ta": C["anova"].format(moi_nhom=m, n=m * k, k=k, **v),
                "can_cu": _can_cu("anova", tb and k == 3)}
    if code in ("bang-cheo", "nhieu-lua-chon-nhom"):
        r = max(2, len((x or {}).get("nhom") or []))
        c = max(2, len((y or {}).get("nhom") or [])) if code == "bang-cheo" else 2
        df = (r - 1) * (c - 1)
        n = n_chi2(df, M["w"])
        return {"n": n, "mo_ta": C["bang-cheo"].format(n=n, **v), "can_cu": _can_cu("bang-cheo", tb and df == 1)}
    if code == "tuong-quan":
        n = n_tuong_quan(M["r"])
        return {"n": n, "mo_ta": C["tuong-quan"].format(n=n, **v), "can_cu": _can_cu("tuong-quan", tb)}
    if code == "t-test-cap":
        n = n_ttest_cap(M["d"])
        return {"n": n, "mo_ta": C["t-test-cap"].format(n=n, **v), "can_cu": _can_cu("t-test-cap", False)}
    return None


def _hypo(key: str, x: dict, y: dict) -> dict:
    g = T["gia_thuyet"][key]
    v = {"x": _giua_cau(x["ten"]), "y": _giua_cau(y["ten"])}
    cap = lambda s: s[:1].upper() + s[1:]
    return {"h0": cap(g["h0"].format(**v)), "h1": cap(g["h1"].format(**v))}


def build_question(q: dict, bien: dict, doi_tuong: str, muc: str = "trung_binh", tong_the: int | None = None) -> dict:
    dang = q.get("dang")
    D = T["dang"].get(dang)
    out = {"dang": dang, "ten_dang": D["ten"] if D else None, "x": q.get("x"), "y": q.get("y"),
           "cau_hoi": None, "cau_hoi_goi_y": None, "gia_thuyet": None, "phep": None, "co_mau": None, "loi": [],
           "canh_bao": []}
    if not D:
        out["loi"].append("Hãy chọn dạng câu hỏi.")
        return out
    x, y = bien.get(q.get("x")), bien.get(q.get("y"))
    if not x or (dang != "mo_ta" and not y):
        out["loi"].append(T["loi"]["thieu_bien"])
        return out
    if y and x["ma"] == y["ma"]:
        out["loi"].append(T["loi"]["trung_bien"])
        return out
    L = T["loi"]
    v = {"x": _giua_cau(x["ten"]), "y": _giua_cau(y["ten"]) if y else "", "doi_tuong": doi_tuong, "nhom": ""}
    kx, ky = x["kieu"], y["kieu"] if y else None

    if dang == "mo_ta":
        code = {"phan_loai": "tan-suat", "nhieu_lua_chon": "nhieu-lua-chon", "dinh_luong": "mo-ta",
                "likert": "trung-binh", "thang_chuan": "thang-do"}[kx]
        an = {"tan-suat": "tan-suat", "nhieu-lua-chon": "nhieu-lua-chon", "mo-ta": "mo-ta", "trung-binh": "trung-binh",
              "thang-do": "thang-do"}[code]
        out.update(cau_hoi_goi_y=D["cau_hoi_nhom" if kx in ("phan_loai", "nhieu_lua_chon") else "cau_hoi_so"].format(**v),
                   phep=_phep(code, an), gia_thuyet={"khong_can": T["gia_thuyet"]["khong_can"]})
    elif dang == "so_sanh":
        if kx != "phan_loai":
            out["loi"].append(L["so_sanh_nhom"].format(x=x["ten"]))
            return out
        if len(x.get("nhom") or []) == 1:
            out["loi"].append(L["so_sanh_mot_nhom"].format(x=x["ten"]))
            return out
        if x.get("nhom"):
            v["nhom"] = f" ({' / '.join(x['nhom'])})"
        k = len(x.get("nhom") or [])
        if ky in SO:
            code = "t-test-doc-lap" if k == 2 else "anova" if k >= 3 else "so-sanh-nhom"
            an = "t-test" if k == 2 else "anova" if k >= 3 else None
            out.update(cau_hoi_goi_y=D["cau_hoi_so"].format(**v), phep=_phep(code, an), gia_thuyet=_hypo("so_sanh_tb", x, y))
        elif ky == "phan_loai":
            out.update(cau_hoi_goi_y=D["cau_hoi_nhom"].format(**v), phep=_phep("bang-cheo", "bang-cheo"),
                       gia_thuyet=_hypo("doc_lap", x, y))
        else:
            out.update(cau_hoi_goi_y=D["cau_hoi_nhom"].format(**v), phep=_phep("nhieu-lua-chon-nhom", "nhieu-lua-chon"),
                       gia_thuyet=_hypo("doc_lap", x, y))
    elif dang == "lien_he":
        if kx in SO and ky in SO:
            out.update(phep=_phep("tuong-quan", "tuong-quan"), gia_thuyet=_hypo("tuong_quan", x, y))
        elif kx == "phan_loai" and ky == "phan_loai":
            out.update(phep=_phep("bang-cheo", "bang-cheo"), gia_thuyet=_hypo("doc_lap", x, y))
        elif "nhieu_lua_chon" in (kx, ky) and "phan_loai" in (kx, ky):
            if kx == "nhieu_lua_chon":            # biến nhóm phải đứng ở vị trí x
                q = {**q, "x": y["ma"], "y": x["ma"]}
                x, y = y, x
            out.update(x=x["ma"], y=y["ma"], phep=_phep("nhieu-lua-chon-nhom", "nhieu-lua-chon"),
                       gia_thuyet=_hypo("doc_lap", x, y))
        else:
            nhom = x if kx == "phan_loai" else y if ky == "phan_loai" else None
            out["loi"].append(L["lien_he_mot_phan_loai"].format(nhom=nhom["ten"]) if nhom
                              else T["nhan_dang"]["canh_bao"]["khong_ro"])
            return out
        out["cau_hoi_goi_y"] = D["cau_hoi_so"].format(**v)
    else:  # truoc_sau
        if kx not in SO or ky not in SO:
            out["loi"].append(L["truoc_sau_so"])
            return out
        if kx != ky:
            out["canh_bao"].append(L["truoc_sau_khac_kieu"].format(x=x["ten"], y=y["ten"]))
        out.update(cau_hoi_goi_y=D["cau_hoi_so"].format(**v), phep=_phep("t-test-cap", "t-test"),
                   gia_thuyet=_hypo("truoc_sau", x, y))

    rieng = " ".join(str(q.get("cau_hoi_rieng") or "").split())
    out["cau_hoi"] = rieng or out["cau_hoi_goi_y"]
    if rieng:
        out["canh_bao"] += [w for w in nhan_dang(rieng)["canh_bao"] if w not in out["canh_bao"]]
    out["co_mau"] = _co_mau(out["phep"]["ma"], x, y, muc, tong_the)
    return out


def build(plan: dict, library: dict) -> dict:
    """Kế hoạch đầy đủ cho giao diện, file Excel và bước thiết kế phiếu."""
    if not isinstance(plan, dict):
        raise LoiPhanTich("Kế hoạch phải là một đối tượng JSON.")
    doi_tuong = " ".join(str(plan.get("doi_tuong") or "").split()) or T["doi_tuong_mac_dinh"]
    bien, loi_bien = _check_vars(plan.get("bien") or [], library)
    muc = plan.get("muc_anh_huong") if plan.get("muc_anh_huong") in T["co_mau"]["muc"] else "trung_binh"
    try:
        tong_the = int(plan.get("tong_the") or 0)
    except (TypeError, ValueError):
        tong_the = 0
    tong_the = tong_the if tong_the >= 10 else None
    cau = [build_question(q, bien, doi_tuong, muc, tong_the) for q in (plan.get("cau_hoi") or [])[:SO_CAU_TOI_DA]]
    for i, c in enumerate(cau, 1):
        c["so"] = i
        for m in (c["x"], c["y"]):
            if m in bien:
                bien[m].setdefault("dung_trong", []).append(i)
    hop_le = [c for c in cau if not c["loi"] and c["co_mau"]]
    lon_nhat = max(hop_le, key=lambda c: c["co_mau"]["n"]) if hop_le else None
    return {"ten_de_tai": plan.get("ten_de_tai") or None, "doi_tuong": doi_tuong, "bien": list(bien.values()),
            "loi_bien": loi_bien, "cau_hoi": cau,
            "co_mau_toi_thieu": {"n": lon_nhat["co_mau"]["n"], "cau": lon_nhat["so"]} if lon_nhat else None,
            "ghi_chu_gia_thuyet": T["gia_thuyet"]["ghi_chu"],
            "gia_dinh_co_mau": T["co_mau"]["gia_dinh"].format(muc=T["co_mau"]["muc"][muc]["ten"]),
            "muc_anh_huong": muc, "tong_the": tong_the,
            "cac_muc_anh_huong": {k: m["ten"] for k, m in T["co_mau"]["muc"].items()},
            "can_cu_co_mau": _references(hop_le),
            "thiet_ke_phieu": design_config(plan, list(bien.values())),
            "dang_cau_hoi": {k: {"ten": d["ten"], "vi_du": d["vi_du"]} for k, d in T["dang"].items()},
            "kieu_bien": T["kieu_bien"]}


def _references(cau: list[dict]) -> dict:
    """Giải thích chung và danh mục tài liệu (APA) của những nguồn thực sự dùng trong kế hoạch."""
    C = T["co_mau"]
    used = {"cohen1988"} | {k for q in cau for k in q["co_mau"]["can_cu"]["nguon_ma"]}
    return {"giai_thich": C["giai_thich"], "tai_lieu": sorted(C["tai_lieu"][k] for k in used)}


def design_config(plan: dict, bien: list[dict]) -> dict:
    """Cấu hình cho /mau-nhap-lieu: biến của kế hoạch thành cột của file Excel mẫu (kèm kế hoạch để tải lên lại)."""
    cfg = {"ten_de_tai": plan.get("ten_de_tai") or None, "cot_chung": [], "thang_do": [],
           "ke_hoach": {k: plan.get(k) for k in ("ten_de_tai", "doi_tuong", "bien", "cau_hoi", "muc_anh_huong", "tong_the")}}
    likert = [b for b in bien if b["kieu"] == "likert"]
    for b in bien:
        if b["kieu"] == "phan_loai":
            cfg["cot_chung"].append({"ten": b["ma"], "cau_hoi": b["ten"], "loai": "nhom", "lua_chon": b.get("nhom") or []})
        elif b["kieu"] == "nhieu_lua_chon":
            cfg["cot_chung"].append({"ten": b["ma"], "cau_hoi": b["ten"], "loai": "nhieu_lua_chon",
                                     "lua_chon": b.get("nhom") or []})
        elif b["kieu"] == "dinh_luong":
            c = {"ten": b["ma"], "cau_hoi": b["ten"], "loai": "so"}
            if "min" in b and "max" in b:
                c.update(min=b["min"], max=b["max"])
            cfg["cot_chung"].append(c)
        elif b["kieu"] == "thang_chuan" and b["thang"] not in cfg["thang_do"]:
            cfg["thang_do"].append(b["thang"])
    if likert:
        cfg["likert"] = {"so_muc": likert[0]["so_muc"],
                         "bien": [{"ma": b["ma"], "ten": b["ten"], "so_cau": b["so_cau"], "dao": []} for b in likert]}
    return cfg


# ---------- Nhận dạng câu hỏi học sinh tự viết ----------

def _norm(s: str) -> str:
    return " ".join(unicodedata.normalize("NFC", s).lower().split())


def nhan_dang(text: str) -> dict:
    N = T["nhan_dang"]
    W = N["canh_bao"]
    t = _norm(text)
    out = {"dang": None, "ten_dang": None, "canh_bao": []}
    if not t:
        return out
    for dang in ("truoc_sau", "so_sanh", "lien_he", "mo_ta"):
        if any(k in t for k in N["tu_khoa"][dang]):
            out["dang"], out["ten_dang"] = dang, T["dang"][dang]["ten"]
            break
    nq = next((w for w in N["nhan_qua"] if w in t), None)
    if nq:
        out["canh_bao"].append(W["nhan_qua"].format(tu=nq))
        if out["dang"] is None:
            out["dang"], out["ten_dang"] = "lien_he", T["dang"]["lien_he"]["ten"]
    if t.count("?") > 1 or re.search(r"\bkhông\b.*\b(và|hay)\b.*\bkhông\s*\??$", t):
        out["canh_bao"].append(W["hai_cau_hoi"])
    if len(t.split()) < 6:
        out["canh_bao"].append(W["qua_ngan"])
    if not t.rstrip().endswith("?"):
        out["canh_bao"].append(W["khong_hoi"])
    if out["dang"] is None:
        out["canh_bao"].append(W["khong_ro"])
    return out


# ---------- File Excel kế hoạch ----------

def _can_cu_text(q: dict) -> str:
    cc = (q.get("co_mau") or {}).get("can_cu")
    if not cc:
        return ""
    parts = [cc["cach_tinh"], "Nguồn: " + "; ".join(cc["nguon"]) + "."]
    if cc.get("doi_chieu"):
        parts.append("Đối chiếu: " + cc["doi_chieu"])
    return "\n".join(parts)

def plan_workbook(built: dict) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Kế hoạch"
    bold = Font(name=FONT, bold=True)
    body = Font(name=FONT)
    wrap = Alignment(wrap_text=True, vertical="top")
    ws["A1"] = built.get("ten_de_tai") or "Kế hoạch nghiên cứu"
    ws["A1"].font = Font(name=FONT, bold=True, size=14)
    ws["A2"] = f"Đối tượng: {built['doi_tuong']}"
    ws["A2"].font = body
    heads = ["STT", "Câu hỏi nghiên cứu", "Dạng câu hỏi", "Giả thuyết H0", "Giả thuyết H1", "Phép phân tích",
             "Biến cần thu thập", "Cỡ mẫu tối thiểu (ước tính)", "Căn cứ cỡ mẫu"]
    widths = [6, 48, 22, 40, 40, 36, 32, 40, 60]
    ten = {b["ma"]: f"{b['ten']} [{b['ma']}] – {b['ten_kieu']}" for b in built["bien"]}
    for j, (hd, w) in enumerate(zip(heads, widths), 1):
        c = ws.cell(row=4, column=j, value=hd)
        c.font, c.fill, c.alignment, c.border = Font(name=FONT, bold=True, color="FFFFFF"), HEADER_FILL, wrap, BORDER
        ws.column_dimensions[c.column_letter].width = w
    r = 5
    for q in built["cau_hoi"]:
        if q["loi"]:
            continue
        gt = q["gia_thuyet"] or {}
        vals = [q["so"], q["cau_hoi"], q["ten_dang"], gt.get("h0") or gt.get("khong_can", ""), gt.get("h1", ""),
                q["phep"]["ten"], "\n".join(ten[m] for m in (q["x"], q["y"]) if m in ten),
                q["co_mau"]["mo_ta"] if q["co_mau"] else "", _can_cu_text(q)]
        for j, val in enumerate(vals, 1):
            c = ws.cell(row=r, column=j, value=val)
            c.font, c.alignment, c.border = body, wrap, BORDER
        r += 1
    notes = [built["ghi_chu_gia_thuyet"], built["gia_dinh_co_mau"]]
    if built.get("co_mau_toi_thieu"):
        notes.insert(0, f"Cỡ mẫu nên thu tối thiểu: khoảng {built['co_mau_toi_thieu']['n']} người "
                        f"(theo câu hỏi {built['co_mau_toi_thieu']['cau']}, câu cần nhiều người nhất).")
    for i, note in enumerate(notes):
        c = ws.cell(row=r + 1 + i, column=1, value=note)
        c.font = bold if i == 0 and built.get("co_mau_toi_thieu") else body
    r += len(notes) + 2
    ws.cell(row=r, column=1, value="Căn cứ khoa học của cỡ mẫu").font = bold
    for note in built["can_cu_co_mau"]["giai_thich"]:
        r += 1
        ws.cell(row=r, column=1, value="• " + note.replace("**", "").replace("*", "")).font = body
    r += 2
    ws.cell(row=r, column=1, value="Tài liệu tham khảo").font = bold
    for ref in built["can_cu_co_mau"]["tai_lieu"]:
        r += 1
        ws.cell(row=r, column=1, value=ref.replace("*", "")).font = body
    ws.freeze_panes = "A5"

    wv = wb.create_sheet("Biến")
    heads = ["Mã cột", "Tên biến", "Loại", "Lựa chọn / số câu / thang", "Dùng trong câu hỏi"]
    for j, (hd, w) in enumerate(zip(heads, [16, 32, 26, 48, 18]), 1):
        c = wv.cell(row=1, column=j, value=hd)
        c.font, c.fill, c.border = Font(name=FONT, bold=True, color="FFFFFF"), HEADER_FILL, BORDER
        wv.column_dimensions[c.column_letter].width = w
    for i, b in enumerate(built["bien"], 2):
        chi_tiet = {"phan_loai": " / ".join(b.get("nhom") or []), "nhieu_lua_chon": " / ".join(b.get("nhom") or []),
                    "likert": f"{b.get('so_cau')} câu, {b.get('so_muc')} mức",
                    "thang_chuan": f"{b.get('thang')} – {b.get('ten_thang') or ''}",
                    "dinh_luong": f"{b['min']:g} – {b['max']:g}" if "min" in b and "max" in b else "Số"}[b["kieu"]]
        for j, val in enumerate([b["ma"], b["ten"], b["ten_kieu"], chi_tiet,
                                 ", ".join(map(str, b.get("dung_trong") or []))], 1):
            c = wv.cell(row=i, column=j, value=val)
            c.font, c.alignment, c.border = body, wrap, BORDER
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
