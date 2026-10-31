"""Thống kê mô tả, tần suất, trung bình – độ lệch chuẩn.
Định dạng đầu ra khớp mục "Dữ liệu đầu vào AI nhận" trong skills-hs/thong-ke-mo-ta, tan-suat, trung-binh-do-lech-chuan."""
import math

import numpy as np
import pandas as pd
from scipy import stats

from . import data_prep
from .utils import LoiPhanTich, display_value, label_of, require_column, to_numeric

KIEU_HOP_LE = {"scale", "ordinal", "nominal", "likert"}


def summary_numeric(x: pd.Series) -> dict:
    """Các chỉ số mô tả cho một biến số. Skewness/Kurtosis dùng công thức hiệu chỉnh như SPSS."""
    x = to_numeric(x).dropna()
    n = len(x)
    out = {"n_valid": n, "mean": None, "sd": None, "se": None, "median": None,
           "min": None, "max": None, "skewness": None, "kurtosis": None}
    if n == 0:
        return out
    sd = x.std(ddof=1) if n > 1 else None
    out.update(mean=x.mean(), sd=sd, median=x.median(), min=x.min(), max=x.max(),
               se=(sd / math.sqrt(n)) if sd is not None else None)
    if n > 2 and x.nunique() > 1:
        out["skewness"] = stats.skew(x, bias=False)
    if n > 3 and x.nunique() > 1:
        out["kurtosis"] = stats.kurtosis(x, fisher=True, bias=False)
    return out


def _sort_key(v):
    try:
        return (0, float(v), "")
    except (TypeError, ValueError):
        return (1, 0.0, str(v))


def order_categories(values, order: list | None) -> tuple[list, str]:
    """Thứ tự các nhóm từ thấp đến cao. Ưu tiên: thứ tự người dùng khai báo → thang thứ bậc tiếng Việt đã biết
    (học lực, mức độ đồng ý…) → số tăng dần / chữ cái."""
    values = list(values)
    if order:
        rank = {str(o).strip().lower(): i for i, o in enumerate(order)}
        return sorted(values, key=lambda v: (rank.get(str(v).strip().lower(), len(rank)), _sort_key(v))), "nguoi_dung"
    known = data_prep.known_order(values)
    if known:
        return known, "tu_nhan"
    return sorted(values, key=_sort_key), "mac_dinh"


def frequency_table(s: pd.Series, var_type: str, labels: dict | None,
                    order: list | None = None) -> tuple[list, int, int, str]:
    n_total = len(s)
    valid = s.dropna()
    n_valid = len(valid)
    counts = valid.map(display_value).value_counts()
    rows, cum = [], 0.0
    ordered, source = order_categories(counts.index, order)
    for v in ordered:
        f = int(counts[v])
        vp = f / n_valid * 100 if n_valid else None
        cum += vp or 0
        rows.append({
            "value": v,
            "label": label_of(v, labels),
            "freq": f,
            "percent": f / n_total * 100 if n_total else None,
            "valid_percent": vp,
            # % tích lũy chỉ có nghĩa với biến có thứ tự
            "cum_percent": cum if var_type in ("ordinal", "likert") else None,
        })
    return rows, n_total, n_valid, source


def frequencies(df: pd.DataFrame, p: dict, value_labels: dict) -> dict:
    """p: {variable, label?, type?, thu_tu?: [nhóm thấp → cao], multiple_response?, cot_lua_chon?, gia_tri_chon?}"""
    if p.get("multiple_response"):
        return _multiple_response(df, p)
    col = p.get("variable")
    require_column(df, col)
    var_type = p.get("type", "nominal")
    if var_type not in KIEU_HOP_LE:
        raise LoiPhanTich(f"Kiểu biến '{var_type}' không hợp lệ. Chọn một trong {sorted(KIEU_HOP_LE)}.")
    rows, n_total, n_valid, source = frequency_table(df[col], var_type, value_labels.get(col), p.get("thu_tu"))
    return {
        "analysis": "tan-suat", "variable": col, "label": p.get("label", col), "type": var_type,
        "multiple_response": False, "n_total": n_total, "n_valid": n_valid,
        "n_missing": n_total - n_valid, "table": rows, "nguon_thu_tu": source,
        "nhom_nho_duoi_5": [r["label"] for r in rows if r["freq"] < 5],
    }


def _multiple_response(df: pd.DataFrame, p: dict) -> dict:
    """Câu chọn nhiều đáp án: mỗi lựa chọn là một cột 0/1. % tính trên số người trả lời."""
    options = p.get("cot_lua_chon") or []
    if not options:
        raise LoiPhanTich("Câu chọn nhiều đáp án cần danh sách 'cot_lua_chon'.")
    chosen = p.get("gia_tri_chon", 1)
    cols = [o["cot"] for o in options]
    for c in cols:
        require_column(df, c)
    block = df[cols].apply(to_numeric)
    answered = block.notna().any(axis=1)
    n_resp = int(answered.sum())
    rows = []
    for o in options:
        f = int((block[o["cot"]] == chosen).sum())
        rows.append({"value": o["cot"], "label": o.get("label", o["cot"]), "freq": f,
                     "percent": f / n_resp * 100 if n_resp else None,
                     "valid_percent": f / n_resp * 100 if n_resp else None, "cum_percent": None})
    return {
        "analysis": "tan-suat", "variable": p.get("variable", "+".join(cols)),
        "label": p.get("label"), "type": "nominal", "multiple_response": True,
        "n_total": len(df), "n_valid": n_resp, "n_missing": len(df) - n_resp, "table": rows,
        "ghi_chu": "% tính trên số người trả lời; một người có thể chọn nhiều đáp án nên tổng có thể vượt 100%.",
    }


def describe(df: pd.DataFrame, p: dict, value_labels: dict) -> dict:
    """p: {variables: [{name, label?, type, thu_tu?: [nhóm thấp → cao]}]}"""
    variables = p.get("variables") or []
    if not variables:
        raise LoiPhanTich("Chưa chọn biến nào để mô tả.")
    out = []
    for v in variables:
        col = v["name"]
        require_column(df, col)
        var_type = v.get("type", "scale")
        if var_type not in KIEU_HOP_LE:
            raise LoiPhanTich(f"Kiểu biến '{var_type}' của cột '{col}' không hợp lệ.")
        s = df[col]
        item = {"name": col, "label": v.get("label", col), "type": var_type,
                "n_valid": int(s.notna().sum()), "n_missing": int(s.isna().sum())}
        if var_type in ("scale", "likert"):
            num = to_numeric(s)
            n_text = int(num.isna().sum() - s.isna().sum())
            if n_text:
                item["canh_bao"] = f"{n_text} ô không phải số đã bị bỏ qua."
            item.update({k: val for k, val in summary_numeric(num).items() if k != "n_valid"})
            item["n_valid"] = int(num.notna().sum())
            item["n_missing"] = len(s) - item["n_valid"]
        if var_type != "scale":
            item["tan_suat"], _, _, item["nguon_thu_tu"] = frequency_table(s, var_type, value_labels.get(col),
                                                                          v.get("thu_tu"))
        out.append(item)
    return {"analysis": "mo-ta", "n_total": len(df), "variables": out}


def means(df: pd.DataFrame, p: dict) -> dict:
    """p: {variables: [{name, label?}], scale_points?: 5|7|null, composite?: {name, label?, cot: [...]}}"""
    variables = p.get("variables") or []
    out = []
    for v in variables:
        require_column(df, v["name"])
        s = summary_numeric(df[v["name"]])
        s["n"] = s.pop("n_valid")
        out.append({"name": v["name"], "label": v.get("label", v["name"]), **s})
    result = {"analysis": "trung-binh", "scale_points": p.get("scale_points"), "variables": out}
    comp = p.get("composite")
    if comp:
        cols = comp.get("cot") or []
        for c in cols:
            require_column(df, c)
        block = df[cols].apply(to_numeric)
        complete = block.dropna()  # chỉ tính cho người trả lời đủ các câu
        score = complete.mean(axis=1)
        s = summary_numeric(score)
        result["composite"] = {"name": comp.get("name"), "label": comp.get("label"),
                               "n": s["n_valid"], "mean": s["mean"], "sd": s["sd"],
                               "n_bi_loai_do_thieu": len(block) - len(complete)}
    return result
