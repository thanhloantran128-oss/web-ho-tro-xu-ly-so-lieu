"""One-way ANOVA kèm Levene, Welch, Tukey HSD / Games-Howell, eta bình phương, Kruskal-Wallis.
Đầu ra khớp skills-hs/anova."""
import math
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from .ttest import _order
from .utils import LoiPhanTich, label_of, norm_value, require_column, to_numeric

NHOM_NHO = 10  # nhóm dưới ngưỡng này bị cảnh báo


def welch_anova(samples: list[np.ndarray]) -> dict:
    """Welch (1951): F, df1, df2, p."""
    k = len(samples)
    n = np.array([len(s) for s in samples], float)
    m = np.array([s.mean() for s in samples])
    v = np.array([s.var(ddof=1) for s in samples])
    if np.any(v == 0):
        return {"F": None, "df1": k - 1, "df2": None, "p": None,
                "ghi_chu": "Có nhóm có phương sai bằng 0 nên không tính được Welch."}
    w = n / v
    sw = w.sum()
    mw = (w * m).sum() / sw
    a = (w * (m - mw) ** 2).sum() / (k - 1)
    lam = ((1 - w / sw) ** 2 / (n - 1)).sum()
    b = 1 + 2 * (k - 2) / (k ** 2 - 1) * lam
    f = a / b
    df2 = (k ** 2 - 1) / (3 * lam)
    return {"F": f, "df1": k - 1, "df2": df2, "p": stats.f.sf(f, k - 1, df2)}


def games_howell(samples, names) -> list:
    k = len(samples)
    out = []
    for i, j in combinations(range(k), 2):
        a, b = samples[i], samples[j]
        vi, vj = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
        diff = a.mean() - b.mean()
        se = math.sqrt(vi + vj)
        if se == 0:
            out.append({"i": names[i], "j": names[j], "mean_diff": diff, "p": None})
            continue
        dfw = (vi + vj) ** 2 / (vi ** 2 / (len(a) - 1) + vj ** 2 / (len(b) - 1))
        q = abs(diff) / se * math.sqrt(2)
        out.append({"i": names[i], "j": names[j], "mean_diff": diff, "se": se, "df": dfw,
                    "p": stats.studentized_range.sf(q, k, dfw)})
    return out


def tukey(samples, names) -> list:
    res = stats.tukey_hsd(*samples)
    ci = res.confidence_interval(confidence_level=0.95)
    out = []
    for i, j in combinations(range(len(samples)), 2):
        out.append({"i": names[i], "j": names[j], "mean_diff": samples[i].mean() - samples[j].mean(),
                    "p": res.pvalue[i, j], "ci95": [ci.low[i, j], ci.high[i, j]]})
    return out


def run(df: pd.DataFrame, p: dict, value_labels: dict) -> dict:
    """p: {dv, factor, dv_label?, factor_label?, posthoc?: 'auto'|'tukey'|'games-howell'}"""
    dv, factor = p.get("dv"), p.get("factor")
    require_column(df, dv)
    require_column(df, factor)
    data = pd.DataFrame({"y": to_numeric(df[dv]), "g": df[factor].map(norm_value)}).dropna()
    levels = sorted(data["g"].unique(), key=_order)
    labels = value_labels.get(factor)
    canh_bao = []
    samples, names, groups = [], [], []
    for lv in levels:
        x = data.loc[data["g"] == lv, "y"].to_numpy(float)
        name = label_of(lv, labels)
        if len(x) < 2:
            canh_bao.append(f"Nhóm '{name}' chỉ có {len(x)} người nên bị loại khỏi phân tích; hãy gộp nhóm.")
            continue
        if len(x) < NHOM_NHO:
            canh_bao.append(f"Nhóm '{name}' chỉ có {len(x)} người; kết quả kém tin cậy, nên cân nhắc gộp nhóm.")
        samples.append(x)
        names.append(name)
        groups.append({"label": name, "n": len(x), "mean": x.mean(), "sd": x.std(ddof=1)})
    k = len(samples)
    if k < 3:
        raise LoiPhanTich(f"ANOVA cần từ 3 nhóm trở lên (hiện có {k} nhóm đủ dữ liệu). Với 2 nhóm hãy dùng t-test.")
    N = sum(len(s) for s in samples)
    allv = np.concatenate(samples)
    grand = allv.mean()
    ssb = sum(len(s) * (s.mean() - grand) ** 2 for s in samples)
    ssw = sum(((s - s.mean()) ** 2).sum() for s in samples)
    df1, df2 = k - 1, N - k
    msw = ssw / df2
    f = (ssb / df1) / msw if msw > 0 else float("nan")
    lev = stats.levene(*samples, center="mean")
    kw = stats.kruskal(*samples)

    choice = p.get("posthoc", "auto")
    if choice == "auto":
        choice = "tukey" if lev.pvalue > 0.05 else "games-howell"
    if choice not in ("tukey", "games-howell"):
        raise LoiPhanTich("posthoc phải là 'auto', 'tukey' hoặc 'games-howell'.")
    pairs = tukey(samples, names) if choice == "tukey" else games_howell(samples, names)

    p_main = stats.f.sf(f, df1, df2)
    welch = welch_anova(samples)
    overall_p = p_main if lev.pvalue > 0.05 else welch["p"]
    return {
        "analysis": "anova",
        "dv": {"name": dv, "label": p.get("dv_label", dv)},
        "factor": {"name": factor, "label": p.get("factor_label", factor)},
        "groups": groups,
        "levene": {"F": lev.statistic, "df1": df1, "df2": df2, "p": lev.pvalue},
        "anova": {"F": f, "df1": df1, "df2": df2, "p": p_main, "eta_sq": ssb / (ssb + ssw),
                  "ss_between": ssb, "ss_within": ssw},
        "welch": welch,
        "kiem_dinh_nen_doc": "anova" if lev.pvalue > 0.05 else "welch",
        "co_y_nghia_tong_the": overall_p is not None and overall_p <= 0.05,
        "posthoc": {"method": "Tukey HSD" if choice == "tukey" else "Games-Howell", "pairs": pairs},
        "nonparametric": {"test": "Kruskal-Wallis", "H": kw.statistic, "df": k - 1, "p": kw.pvalue},
        "canh_bao": canh_bao,
        "n_bi_loai_do_thieu": int(len(df) - len(data)),
    }
