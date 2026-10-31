"""Bảng chéo (Crosstabs) và kiểm định Chi-square độc lập. Đầu ra khớp skills-hs/bang-cheo."""
import math

import numpy as np
import pandas as pd
from scipy import stats

from .descriptives import order_categories
from .utils import LoiPhanTich, display_value, label_of, require_column


def run(df: pd.DataFrame, p: dict, value_labels: dict) -> dict:
    """p: {hang, cot, hang_label?, cot_label?, thu_tu_hang?, thu_tu_cot?}"""
    r, c = p.get("hang"), p.get("cot")
    require_column(df, r)
    require_column(df, c)
    if r == c:
        raise LoiPhanTich("Biến hàng và biến cột đang là cùng một cột. Hãy chọn hai biến khác nhau.")
    data = pd.DataFrame({"r": df[r].map(lambda v: v if pd.isna(v) else display_value(v)),
                         "c": df[c].map(lambda v: v if pd.isna(v) else display_value(v))}).dropna()
    rows, _ = order_categories(data["r"].unique(), p.get("thu_tu_hang"))
    cols, _ = order_categories(data["c"].unique(), p.get("thu_tu_cot"))
    if len(rows) < 2 or len(cols) < 2:
        raise LoiPhanTich("Mỗi biến cần ít nhất 2 nhóm có dữ liệu để lập bảng chéo.")
    obs = pd.crosstab(data["r"], data["c"]).reindex(index=rows, columns=cols, fill_value=0).to_numpy()
    n = int(obs.sum())
    chi2, pval, dof, expected = stats.chi2_contingency(obs, correction=False)
    k = min(len(rows), len(cols)) - 1
    lt5 = expected < 5
    fisher = None
    if obs.shape == (2, 2) and lt5.any():
        fisher = stats.fisher_exact(obs).pvalue
    row_tot, col_tot = obs.sum(axis=1), obs.sum(axis=0)
    rl, cl = value_labels.get(r), value_labels.get(c)
    return {
        "analysis": "bang-cheo",
        "hang": {"name": r, "label": p.get("hang_label") or r, "nhom": [label_of(v, rl) for v in rows]},
        "cot": {"name": c, "label": p.get("cot_label") or c, "nhom": [label_of(v, cl) for v in cols]},
        "n": n, "n_bi_loai_do_thieu": int(len(df) - len(data)),
        "tan_so": obs.tolist(), "tong_hang": row_tot.tolist(), "tong_cot": col_tot.tolist(),
        "pct_hang": (obs / row_tot[:, None] * 100).tolist(),
        "pct_cot": (obs / col_tot[None, :] * 100).tolist(),
        "ky_vong": expected.tolist(),
        "chi2": chi2, "df": int(dof), "p": pval,
        "cramers_v": math.sqrt(chi2 / (n * k)) if n and k else None, "df_v": k,
        "pct_o_ky_vong_nho": float(lt5.mean() * 100), "ky_vong_nho_nhat": float(expected.min()),
        "fisher_p": fisher,
        "kiem_dinh_nen_doc": "fisher" if fisher is not None else "chi2",
    }
