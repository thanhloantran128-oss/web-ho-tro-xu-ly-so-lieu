"""Kiểm định t: one-sample, independent, paired.
Đầu ra khớp skills-hs/t-test. Levene dùng trung bình (center='mean') giống SPSS."""
import math

import numpy as np
import pandas as pd
from scipy import stats

from .utils import LoiPhanTich, label_of, norm_value, require_column, to_numeric


def _ci(diff: float, se: float, df: float, conf: float = 0.95) -> list:
    t = stats.t.ppf(1 - (1 - conf) / 2, df)
    return [diff - t * se, diff + t * se]


def _desc(x: np.ndarray, label: str) -> dict:
    return {"label": label, "n": len(x), "mean": float(np.mean(x)),
            "sd": float(np.std(x, ddof=1)) if len(x) > 1 else None}


def _skew(x: np.ndarray):
    return float(stats.skew(x, bias=False)) if len(x) > 2 and np.ptp(x) > 0 else None


def run(df: pd.DataFrame, p: dict, value_labels: dict) -> dict:
    kind = p.get("type")
    if kind == "independent":
        return independent(df, p, value_labels)
    if kind == "one-sample":
        return one_sample(df, p)
    if kind == "paired":
        return paired(df, p)
    raise LoiPhanTich("Loại t-test phải là 'independent', 'one-sample' hoặc 'paired'.")


def independent(df: pd.DataFrame, p: dict, value_labels: dict) -> dict:
    """p: {dv, group, nhom?: [giá trị nhóm 1, giá trị nhóm 2], dv_label?}"""
    dv, group = p.get("dv"), p.get("group")
    require_column(df, dv)
    require_column(df, group)
    data = pd.DataFrame({"y": to_numeric(df[dv]), "g": df[group].map(norm_value)}).dropna()
    labels = value_labels.get(group)
    levels = [_level_of(v, labels) for v in p["nhom"]] if p.get("nhom") else sorted(data["g"].unique(), key=_order)
    if len(levels) != 2:
        raise LoiPhanTich(
            f"Biến nhóm '{group}' có {len(levels)} nhóm. Independent t-test cần đúng 2 nhóm; "
            "hãy chọn 2 nhóm cần so sánh hoặc dùng ANOVA khi có từ 3 nhóm.")
    a = data.loc[data["g"] == levels[0], "y"].to_numpy(float)
    b = data.loc[data["g"] == levels[1], "y"].to_numpy(float)
    if len(a) < 2 or len(b) < 2:
        raise LoiPhanTich("Mỗi nhóm cần ít nhất 2 người có dữ liệu.")
    n1, n2 = len(a), len(b)
    m1, m2 = a.mean(), b.mean()
    v1, v2 = a.var(ddof=1), b.var(ddof=1)
    diff = m1 - m2

    # Giả định phương sai bằng nhau (Student)
    sp2 = ((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)
    se = math.sqrt(sp2 * (1 / n1 + 1 / n2))
    df_s = n1 + n2 - 2
    t_s = diff / se if se > 0 else float("nan")
    p_s = 2 * stats.t.sf(abs(t_s), df_s)

    # Không giả định phương sai bằng nhau (Welch)
    se_w = math.sqrt(v1 / n1 + v2 / n2)
    df_w = (v1 / n1 + v2 / n2) ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)) if se_w > 0 else float("nan")
    t_w = diff / se_w if se_w > 0 else float("nan")
    p_w = 2 * stats.t.sf(abs(t_w), df_w)

    lev = stats.levene(a, b, center="mean")
    mw = stats.mannwhitneyu(a, b, alternative="two-sided")
    return {
        "analysis": "t-test", "type": "independent",
        "dv": {"name": dv, "label": p.get("dv_label", dv)},
        "groups": [_desc(a, label_of(levels[0], labels)), _desc(b, label_of(levels[1], labels))],
        "test_value": None,
        "levene": {"F": lev.statistic, "df1": 1, "df2": n1 + n2 - 2, "p": lev.pvalue},
        "student": {"t": t_s, "df": df_s, "p": p_s, "mean_diff": diff, "ci95": _ci(diff, se, df_s)},
        "welch": {"t": t_w, "df": df_w, "p": p_w, "mean_diff": diff, "ci95": _ci(diff, se_w, df_w)},
        "dong_nen_doc": "student" if lev.pvalue > 0.05 else "welch",
        "cohens_d": diff / math.sqrt(sp2) if sp2 > 0 else None,
        "normality": {"skewness_by_group": [_skew(a), _skew(b)]},
        "nonparametric": {"test": "Mann-Whitney U", "U": mw.statistic, "p": mw.pvalue,
                          "ghi_chu": "U tính cho nhóm thứ nhất"},
        "n_bi_loai_do_thieu": int(len(df) - len(data)),
    }


def one_sample(df: pd.DataFrame, p: dict) -> dict:
    """p: {dv, test_value}"""
    dv = p.get("dv")
    require_column(df, dv)
    if p.get("test_value") is None:
        raise LoiPhanTich("One-sample t-test cần 'test_value' (ví dụ 3 = mức trung lập thang 5 điểm).")
    mu = float(p["test_value"])
    x = to_numeric(df[dv]).dropna().to_numpy(float)
    n = len(x)
    if n < 2:
        raise LoiPhanTich("Cần ít nhất 2 người có dữ liệu.")
    m, sd = x.mean(), x.std(ddof=1)
    se = sd / math.sqrt(n)
    diff = m - mu
    t = diff / se if se > 0 else float("nan")
    dfree = n - 1
    nonzero = x - mu
    wil = stats.wilcoxon(nonzero) if np.any(nonzero != 0) else None
    return {
        "analysis": "t-test", "type": "one-sample",
        "dv": {"name": dv, "label": p.get("dv_label", dv)},
        "groups": [_desc(x, p.get("dv_label", dv))],
        "test_value": mu,
        "student": {"t": t, "df": dfree, "p": 2 * stats.t.sf(abs(t), dfree),
                    "mean_diff": diff, "ci95": _ci(diff, se, dfree)},
        "cohens_d": diff / sd if sd > 0 else None,
        "normality": {"skewness_by_group": [_skew(x)]},
        "nonparametric": ({"test": "Wilcoxon signed-rank (một mẫu)", "W": wil.statistic, "p": wil.pvalue}
                          if wil else None),
        "n_bi_loai_do_thieu": int(len(df) - n),
    }


def paired(df: pd.DataFrame, p: dict) -> dict:
    """p: {dv: cột lần đo 1, dv2: cột lần đo 2, labels?: [nhãn 1, nhãn 2]}"""
    c1, c2 = p.get("dv"), p.get("dv2")
    require_column(df, c1)
    require_column(df, c2)
    data = pd.DataFrame({"a": to_numeric(df[c1]), "b": to_numeric(df[c2])}).dropna()
    n = len(data)
    if n < 2:
        raise LoiPhanTich("Cần ít nhất 2 người có đủ dữ liệu ở cả hai lần đo.")
    a, b = data["a"].to_numpy(float), data["b"].to_numpy(float)
    d = a - b
    md, sdd = d.mean(), d.std(ddof=1)
    se = sdd / math.sqrt(n)
    t = md / se if se > 0 else float("nan")
    dfree = n - 1
    labels = p.get("labels") or [c1, c2]
    wil = stats.wilcoxon(d) if np.any(d != 0) else None
    r = stats.pearsonr(a, b) if np.ptp(a) > 0 and np.ptp(b) > 0 else None
    return {
        "analysis": "t-test", "type": "paired",
        "dv": {"name": f"{c1} – {c2}", "label": p.get("dv_label", "điểm số")},
        "groups": [_desc(a, labels[0]), _desc(b, labels[1])],
        "test_value": None,
        "diff_mean": md, "diff_sd": sdd,
        "student": {"t": t, "df": dfree, "p": 2 * stats.t.sf(abs(t), dfree),
                    "mean_diff": md, "ci95": _ci(md, se, dfree)},
        "cohens_d": md / sdd if sdd > 0 else None,  # d_z = trung bình hiệu số / ĐLC hiệu số
        "tuong_quan_cap": {"r": r.statistic, "p": r.pvalue} if r else None,
        "normality": {"skewness_of_diff": _skew(d)},
        "nonparametric": ({"test": "Wilcoxon signed-rank", "W": wil.statistic, "p": wil.pvalue} if wil else None),
        "n_bi_loai_do_thieu": int(len(df) - n),
    }


def _level_of(v, labels: dict | None):
    """Nhóm học sinh gõ có thể là mã (1) hoặc nhãn (Nam): đổi nhãn về mã để lọc dữ liệu."""
    key = norm_value(v)
    for code, lab in (labels or {}).items():
        if str(lab).strip().lower() == str(v).strip().lower():
            return norm_value(code)
    return key


def _order(v):
    try:
        return (0, float(v), "")
    except (TypeError, ValueError):
        return (1, 0.0, str(v))
