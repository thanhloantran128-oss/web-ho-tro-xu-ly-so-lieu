"""Tương quan Pearson / Spearman giữa các biến định lượng. Đầu ra khớp skills-hs/tuong-quan.
Mỗi cặp dùng những người có đủ dữ liệu ở cả hai biến (pairwise)."""
import math
from itertools import combinations

import pandas as pd
from scipy import stats

from .utils import LoiPhanTich, require_column, to_numeric

PHUONG_PHAP = {"pearson", "spearman"}


def _ci_pearson(r: float, n: int):
    """Khoảng tin cậy 95% của r theo biến đổi Fisher z."""
    if n <= 3 or abs(r) >= 1:
        return None
    z, se = math.atanh(r), 1 / math.sqrt(n - 3)
    return [math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)]


def run(df: pd.DataFrame, p: dict, value_labels: dict) -> dict:
    """p: {bien: [cột…] (≥ 2), nhan?: {cột: tên hiển thị}, phuong_phap: 'pearson' | 'spearman'}"""
    cols = list(dict.fromkeys(p.get("bien") or []))
    if len(cols) < 2:
        raise LoiPhanTich("Tương quan cần ít nhất 2 biến.")
    method = p.get("phuong_phap", "pearson")
    if method not in PHUONG_PHAP:
        raise LoiPhanTich("Phương pháp phải là 'pearson' hoặc 'spearman'.")
    for c in cols:
        require_column(df, c)
    data = df[cols].apply(to_numeric)
    labels = {c: (p.get("nhan") or {}).get(c) or c for c in cols}
    pairs = []
    for a, b in combinations(cols, 2):
        xy = data[[a, b]].dropna()
        n = len(xy)
        row = {"x": a, "y": b, "x_label": labels[a], "y_label": labels[b], "n": n, "r": None, "p": None, "ci95": None}
        if n >= 3 and xy[a].nunique() > 1 and xy[b].nunique() > 1:
            res = stats.pearsonr(xy[a], xy[b]) if method == "pearson" else stats.spearmanr(xy[a], xy[b])
            row.update(r=float(res.statistic), p=float(res.pvalue), df=n - 2,
                       ci95=_ci_pearson(float(res.statistic), n) if method == "pearson" else None)
        pairs.append(row)
    m = sum(1 for x in pairs if x["p"] is not None)
    for x in pairs:
        x["p_bonferroni"] = min(1.0, x["p"] * m) if x["p"] is not None else None
    desc = []
    for c in cols:
        v = data[c].dropna()
        desc.append({"name": c, "label": labels[c], "n": int(len(v)), "mean": v.mean() if len(v) else None,
                     "sd": v.std(ddof=1) if len(v) > 1 else None,
                     "skewness": float(stats.skew(v, bias=False)) if len(v) > 2 and v.nunique() > 1 else None})
    return {"analysis": "tuong-quan", "phuong_phap": method, "bien": desc, "cap": pairs, "so_cap_kiem_dinh": m}
