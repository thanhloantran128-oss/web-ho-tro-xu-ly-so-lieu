"""Kiểm tra điều kiện áp dụng t-test và ANOVA theo loại thang đo (lý thuyết thống kê).

- Biến phụ thuộc (dv): phải là biến định lượng (khoảng/tỷ lệ) hoặc điểm trung bình của thang nhiều câu.
  Biến chữ, nhị phân, hằng số → CHẶN. Một câu Likert / biến thứ bậc ít mức → CẢNH BÁO (kèm kiểm định phi tham số).
- Biến nhóm: phải là biến phân loại ít nhóm. Biến số đo liên tục → CHẶN; quá nhiều nhóm → CẢNH BÁO.
- Paired: hai cột khác nhau, cùng thang. One-sample: giá trị so sánh nằm trong khoảng của biến.
Lời văn nằm trong giai-thich/rang-buoc.yaml.
"""
from pathlib import Path

import pandas as pd
import yaml

from .utils import LoiPhanTich, display_value, to_numeric

R = yaml.safe_load((Path(__file__).resolve().parents[2] / "giai-thich" / "rang-buoc.yaml").read_text(encoding="utf-8"))
NG = R["nguong"]


def _fmt(x) -> str:
    v = display_value(x)
    return str(v).replace(".", ",") if isinstance(v, float) else str(v)


def _score_columns(scale_reports: list) -> dict:
    """{tên cột điểm: Cronbach's α} của các thang đã chấm – các cột này được coi là biến định lượng."""
    out = {}
    for rep in scale_reports or []:
        alphas = (rep.get("kiem_tra") or {}).get("cronbach") or {}
        for code, kq in (rep.get("ket_qua") or {}).items():
            out[kq["cot_diem"]] = alphas.get(code)
    return out


KHONG_DINH_LUONG = {"nominal", "multi", "skip"}
TEN_LOAI = {"nominal": "định danh", "ordinal": "thứ bậc", "likert": "Likert", "scale": "định lượng",
            "multi": "câu nhiều lựa chọn", "skip": "bỏ qua"}


def _loai(types: dict, col) -> str | None:
    return (types.get(col) or {}).get("loai") if col else None


def _check_dv(df: pd.DataFrame, col: str, scores: dict, errors: list, warns: list, loai: str | None = None):
    if col not in df.columns:
        return
    if loai in KHONG_DINH_LUONG and col not in scores:
        errors.append(R["chan"]["khai_bao_khong_dinh_luong"].format(bien=col, loai=TEN_LOAI[loai]))
        return
    s = df[col].dropna()
    num = to_numeric(s)
    if num.notna().sum() < max(1, len(s) / 2):
        errors.append(R["chan"]["bien_chu"].format(bien=col))
        return
    n_text = int(num.isna().sum())
    if n_text:
        warns.append(R["canh_bao"]["khong_phai_so"].format(n=n_text, bien=col))
    num = num.dropna()
    uniq = sorted(num.unique())
    if len(uniq) == 1:
        errors.append(R["chan"]["bien_hang_so"].format(bien=col, gia_tri=_fmt(uniq[0])))
        return
    if len(uniq) == 2:
        errors.append(R["chan"]["bien_nhi_phan"].format(bien=col, gia_tri=" và ".join(_fmt(u) for u in uniq)))
        return
    if col in scores:
        a = scores[col]
        if a is not None and a < NG["alpha_thap"]:
            warns.append(("do_tin_cay_thap", {"bien": col, "alpha": f"{a:.2f}".lstrip("0").replace(".", ",")}))
        return
    is_int = bool((num == num.round()).all())
    if loai in ("likert", "ordinal") or (loai is None and is_int and len(uniq) <= NG["so_muc_thu_bac"]):
        warns.append(("bien_thu_bac", {"bien": col, "k": len(uniq), "min": _fmt(uniq[0]), "max": _fmt(uniq[-1])}))


def _check_group(df: pd.DataFrame, col: str, analysis: str, errors: list, warns: list, loai: str | None = None):
    if col not in df.columns:
        return
    s = df[col].dropna()
    k = int(s.nunique())
    num = to_numeric(s)
    numeric = num.notna().all() and len(s) > 0
    if loai == "multi":
        errors.append(R["chan"]["khai_bao_nhieu_lua_chon"].format(bien=col))
        return
    if loai == "scale":
        errors.append(R["chan"]["khai_bao_nhom_dinh_luong"].format(nhom=col))
        return
    if loai is not None:   # đã khai báo là biến phân loại
        continuous = False
    else:
        continuous = numeric and (not bool((num == num.round()).all()) or k > NG["so_nhom_toi_da_bien_nhom"])
    if continuous:
        errors.append(R["chan"]["nhom_la_so_do"].format(nhom=col, k=k))
    elif analysis == "anova" and k > NG["so_nhom_toi_da_bien_nhom"]:
        warns.append(R["canh_bao"]["qua_nhieu_nhom"].format(nhom=col, k=k))


def _check_crosstab(df: pd.DataFrame, p: dict, errors: list, warns: list, types: dict):
    r, c = p.get("hang"), p.get("cot")
    if r and r == c:
        errors.append(R["chan"]["bang_cheo_trung_cot"].format(bien=r))
        return
    for col in (r, c):
        if col not in df.columns:
            continue
        s = df[col].dropna()
        k = int(s.nunique())
        num = to_numeric(s)
        loai = _loai(types, col)
        if loai == "multi":
            errors.append(R["chan"]["khai_bao_nhieu_lua_chon"].format(bien=col))
        elif loai == "scale" or (loai is None and num.notna().all() and len(s)
                                 and (not bool((num == num.round()).all()) or k > NG["so_nhom_toi_da_bien_nhom"])):
            errors.append(R["chan"]["bang_cheo_so_do"].format(bien=col, k=k))
        elif k > NG["so_nhom_toi_da_bien_nhom"]:
            warns.append(R["canh_bao"]["bang_cheo_nhieu_nhom"].format(bien=col, k=k))


def _check_correlation(df: pd.DataFrame, p: dict, scores: dict, errors: list, warns: list, types: dict):
    cols = [c for c in dict.fromkeys(p.get("bien") or []) if c in df.columns]
    if len(cols) < 2:
        errors.append(R["chan"]["tuong_quan_it_bien"])
        return
    for col in cols:
        s = df[col].dropna()
        num = to_numeric(s)
        loai = "scale" if col in scores else _loai(types, col)
        if loai in KHONG_DINH_LUONG or num.notna().sum() < max(1, len(s) / 2):
            errors.append(R["chan"]["tuong_quan_chu"].format(bien=col))
            continue
        num = num.dropna()
        uniq = sorted(num.unique())
        if len(uniq) == 1:
            errors.append(R["chan"]["bien_hang_so"].format(bien=col, gia_tri=_fmt(uniq[0])))
        elif len(uniq) == 2:
            warns.append(R["canh_bao"]["tuong_quan_nhi_phan"].format(bien=col))
        elif p.get("phuong_phap", "pearson") == "pearson" and col not in scores and (
                loai in ("likert", "ordinal")
                or (loai is None and bool((num == num.round()).all()) and len(uniq) <= NG["so_muc_thu_bac"])):
            warns.append(R["canh_bao"]["tuong_quan_thu_bac"].format(bien=col, k=len(uniq), min=_fmt(uniq[0]),
                                                                   max=_fmt(uniq[-1])))
        a = scores.get(col)
        if a is not None and a < NG["alpha_thap"]:
            warns.append(("do_tin_cay_thap", {"bien": col, "alpha": f"{a:.2f}".lstrip("0").replace(".", ",")}))


def check_before(analysis: str, df: pd.DataFrame, p: dict, scale_reports: list) -> list:
    """Chạy trước phân tích. Lỗi nghiêm trọng → LoiPhanTich (không chạy). Trả về cảnh báo cần p phi tham số sau.
    p["kieu_bien"]: loại thang đo học sinh đã khai báo {cột: {"loai": …}} – ưu tiên hơn suy đoán từ dữ liệu."""
    types = p.get("kieu_bien") or {}
    if analysis in ("bang-cheo", "tuong-quan"):
        errors, warns = [], []
        if analysis == "bang-cheo":
            _check_crosstab(df, p, errors, warns, types)
        else:
            _check_correlation(df, p, _score_columns(scale_reports), errors, warns, types)
        if errors:
            raise LoiPhanTich("\n\n".join(dict.fromkeys(errors)))
        return warns
    if analysis not in ("t-test", "anova"):
        return []
    errors, warns = [], []
    scores = _score_columns(scale_reports)
    dv = p.get("dv")
    _check_dv(df, dv, scores, errors, warns, _loai(types, dv))
    kind = p.get("type")
    if analysis == "anova" or kind == "independent":
        group = p.get("factor") if analysis == "anova" else p.get("group")
        if group and group == dv:
            errors.append(R["chan"]["trung_cot"].format(bien=dv))
        else:
            _check_group(df, group, analysis, errors, warns, _loai(types, group))
    if analysis == "t-test" and kind == "paired":
        dv2 = p.get("dv2")
        if dv2 == dv:
            errors.append(R["chan"]["paired_trung_cot"].format(bien=dv))
        else:
            _check_dv(df, dv2, scores, errors, warns, _loai(types, dv2))
            if not errors and dv in df and dv2 in df:
                a, b = to_numeric(df[dv]).dropna(), to_numeric(df[dv2]).dropna()
                ra, rb = a.max() - a.min(), b.max() - b.min()
                if min(ra, rb) > 0 and max(ra, rb) / min(ra, rb) > 2:
                    warns.append(R["canh_bao"]["paired_khac_thang"].format(
                        a=f"{_fmt(a.min())}–{_fmt(a.max())}", b=f"{_fmt(b.min())}–{_fmt(b.max())}"))
    if analysis == "t-test" and kind == "one-sample" and p.get("test_value") is not None and dv in df:
        v = to_numeric(df[dv]).dropna()
        mu = float(p["test_value"])
        if len(v) and not (v.min() <= mu <= v.max()):
            warns.append(R["canh_bao"]["one_sample_ngoai_khoang"].format(mu=_fmt(mu), min=_fmt(v.min()), max=_fmt(v.max())))
    if errors:
        raise LoiPhanTich("\n\n".join(dict.fromkeys(errors)))
    return warns


def finish(warns: list, result: dict) -> list[str]:
    """Điền p của kiểm định phi tham số vào cảnh báo (chỉ có sau khi phân tích) và thêm cảnh báo cỡ nhóm."""
    np_ = result.get("nonparametric") or {}
    p_pt = np_.get("p")
    p_txt = "—" if p_pt is None else ("< ,001" if p_pt < 0.001 else "= " + f"{p_pt:.3f}".lstrip("0").replace(".", ","))
    out = []
    for w in warns:
        if isinstance(w, tuple):
            key, v = w
            out.append(R["canh_bao"][key].format(ten_pt=np_.get("test", "kiểm định phi tham số"), p_pt=p_txt, **v))
        else:
            out.append(w)
    if result.get("analysis") == "tuong-quan":
        if result.get("phuong_phap") == "pearson":
            for b in result.get("bien", []):
                if b.get("skewness") is not None and abs(b["skewness"]) > 2:
                    out.append(R["canh_bao"]["tuong_quan_lech"].format(
                        bien=b["label"], skew=f"{b['skewness']:.2f}".replace(".", ",").replace("-", "−")))
        for c in result.get("cap", []):
            if c["n"] < 10:
                out.append(R["canh_bao"]["tuong_quan_n_nho"].format(x=c["x_label"], y=c["y_label"], n=c["n"]))
    if result.get("analysis") == "t-test" and result.get("type") == "independent":
        for g in result.get("groups", []):
            if g["n"] < NG["nhom_rat_nho"]:
                out.append(R["canh_bao"]["nhom_rat_nho"].format(ten_nhom=g["label"], n=g["n"]))
        out.append(R["canh_bao"]["doc_lap"])
    return out
