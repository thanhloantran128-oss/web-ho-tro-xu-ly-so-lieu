import numpy as np
import pandas as pd
import pytest
from scipy import stats

from app import anova, ttest
from app.utils import LoiPhanTich

RNG = np.random.default_rng(42)


def test_independent_hand_calculated():
    # a: m=3, var=2.5; b: m=6, var=10 → sp²=6.25, se=1.5811, t=−1.8974, df=8; Welch df=5.882
    df = pd.DataFrame({"y": [1, 2, 3, 4, 5, 2, 4, 6, 8, 10], "g": [1] * 5 + [2] * 5})
    r = ttest.run(df, {"type": "independent", "dv": "y", "group": "g"}, {})
    assert r["student"]["t"] == pytest.approx(-1.897367, abs=1e-5)
    assert r["student"]["df"] == 8
    assert r["welch"]["df"] == pytest.approx(5.882353, abs=1e-5)
    assert r["cohens_d"] == pytest.approx(-3 / 2.5)


def test_independent_matches_scipy():
    a, b = RNG.normal(3.5, 0.7, 40), RNG.normal(3.8, 1.1, 55)
    df = pd.DataFrame({"y": np.r_[a, b], "g": ["Nam"] * 40 + ["Nữ"] * 55})
    r = ttest.run(df, {"type": "independent", "dv": "y", "group": "g"}, {})
    s = stats.ttest_ind(a, b)
    w = stats.ttest_ind(a, b, equal_var=False)
    lev = stats.levene(a, b, center="mean")
    assert r["student"]["t"] == pytest.approx(s.statistic)
    assert r["student"]["p"] == pytest.approx(s.pvalue)
    assert r["welch"]["t"] == pytest.approx(w.statistic)
    assert r["welch"]["p"] == pytest.approx(w.pvalue)
    assert r["levene"]["p"] == pytest.approx(lev.pvalue)
    assert r["groups"][0]["label"] == "Nam"


def test_independent_rejects_three_groups():
    df = pd.DataFrame({"y": range(9), "g": [1, 2, 3] * 3})
    with pytest.raises(LoiPhanTich):
        ttest.run(df, {"type": "independent", "dv": "y", "group": "g"}, {})


def test_one_sample_and_paired_match_scipy():
    x, y = RNG.normal(3.7, 0.7, 60), RNG.normal(3.5, 0.7, 60)
    df = pd.DataFrame({"x": x, "y": y})
    r1 = ttest.run(df, {"type": "one-sample", "dv": "x", "test_value": 3}, {})
    s1 = stats.ttest_1samp(x, 3)
    assert r1["student"]["t"] == pytest.approx(s1.statistic)
    assert r1["student"]["p"] == pytest.approx(s1.pvalue)
    r2 = ttest.run(df, {"type": "paired", "dv": "x", "dv2": "y"}, {})
    s2 = stats.ttest_rel(x, y)
    assert r2["student"]["t"] == pytest.approx(s2.statistic)
    assert r2["cohens_d"] == pytest.approx((x - y).mean() / (x - y).std(ddof=1))


def _exact(m, s, n):
    z = RNG.normal(size=n)
    z = (z - z.mean()) / z.std(ddof=1)
    return m + s * z


def test_anova_matches_scipy_and_eta():
    g = [RNG.normal(3.5, 0.7, 30), RNG.normal(3.7, 0.7, 35), RNG.normal(3.9, 0.6, 28)]
    df = pd.DataFrame({"y": np.concatenate(g), "k": [10] * 30 + [11] * 35 + [12] * 28})
    r = anova.run(df, {"dv": "y", "factor": "k"}, {})
    f = stats.f_oneway(*g)
    assert r["anova"]["F"] == pytest.approx(f.statistic)
    assert r["anova"]["p"] == pytest.approx(f.pvalue)
    allv = np.concatenate(g)
    sst = ((allv - allv.mean()) ** 2).sum()
    assert r["anova"]["ss_between"] + r["anova"]["ss_within"] == pytest.approx(sst)
    assert r["nonparametric"]["p"] == pytest.approx(stats.kruskal(*g).pvalue)
    assert len(r["posthoc"]["pairs"]) == 3


def test_welch_anova_two_groups_equals_welch_t_squared():
    a, b = RNG.normal(0, 1, 20), RNG.normal(0.8, 2, 35)
    w = anova.welch_anova([a, b])
    t = stats.ttest_ind(a, b, equal_var=False)
    assert w["F"] == pytest.approx(t.statistic ** 2)
    assert w["p"] == pytest.approx(t.pvalue)


def test_games_howell_and_tukey_two_groups_equal_t_tests():
    a, b = RNG.normal(0, 1, 20), RNG.normal(0.8, 2, 35)
    gh = anova.games_howell([a, b], ["a", "b"])[0]
    assert gh["p"] == pytest.approx(stats.ttest_ind(a, b, equal_var=False).pvalue, rel=1e-4)
    tk = anova.tukey([a, b], ["a", "b"])[0]
    assert tk["p"] == pytest.approx(stats.ttest_ind(a, b).pvalue, rel=1e-4)


def test_welch_anova_skill_example():
    # Ví dụ trong skills-hs/anova: F(2; 131,2) = 6,62; ANOVA F(2, 197) = 6,35; η² = 0,061
    g = [_exact(3.48, 0.70, 70), _exact(3.66, 0.68, 66), _exact(3.89, 0.61, 64)]
    w = anova.welch_anova(g)
    assert w["F"] == pytest.approx(6.62, abs=0.01)
    assert w["df2"] == pytest.approx(131.2, abs=0.1)
    df = pd.DataFrame({"y": np.concatenate(g), "k": [10] * 70 + [11] * 66 + [12] * 64})
    r = anova.run(df, {"dv": "y", "factor": "k"}, {})
    assert r["anova"]["F"] == pytest.approx(6.35, abs=0.01)
    assert r["anova"]["eta_sq"] == pytest.approx(0.061, abs=0.001)


def test_anova_rejects_two_groups():
    df = pd.DataFrame({"y": range(10), "g": [1, 2] * 5})
    with pytest.raises(LoiPhanTich):
        anova.run(df, {"dv": "y", "factor": "g"}, {})
