import numpy as np
import pandas as pd
import pytest
from scipy import stats

from app import explain_rules as ex
from app import multiresponse as mr
from app.utils import LoiPhanTich

OPTS = ["Facebook", "TikTok", "Bạn bè, người thân"]


def _text_df():
    return pd.DataFrame({"kenh": ["Facebook, TikTok", "Bạn bè, người thân", "Facebook, Bạn bè, người thân, Hội chợ",
                                  None, "TikTok"],
                         "gt": ["Nam", "Nữ", "Nữ", "Nam", "Nam"]})


def test_text_with_known_options_keeps_commas_inside_option():
    r = mr.run(_text_df(), {"dang": "van_ban", "cot": "kenh", "cac_lua_chon": OPTS}, {})
    by = {row["label"]: row for row in r["table"]}
    assert r["n_tra_loi"] == 4 and r["n_khong_tra_loi"] == 1
    assert by["Bạn bè, người thân"]["freq"] == 2  # không bị tách thành "Bạn bè" và "người thân"
    assert by["Facebook"]["pct_nguoi"] == pytest.approx(50)
    assert by["Khác"]["freq"] == 1 and r["so_cau_tra_loi_khac"] == 1
    assert r["tong_luot_chon"] == 7
    assert sum(row["pct_luot"] for row in r["table"]) == pytest.approx(100)
    assert r["so_lua_chon_tb"] == pytest.approx(7 / 4)
    assert r["table"][-1]["label"] == "Khác"


def test_text_without_known_options_warns():
    r = mr.run(_text_df(), {"dang": "van_ban", "cot": "kenh"}, {})
    labels = {row["label"] for row in r["table"]}
    assert "Bạn bè" in labels and r["canh_bao"]


def test_binary_format():
    df = pd.DataFrame({"fb": [1, 1, 0, np.nan], "tt": [1, 0, 0, np.nan]})
    r = mr.run(df, {"dang": "nhi_phan", "cot_lua_chon": [{"cot": "fb", "label": "Facebook"},
                                                         {"cot": "tt", "label": "TikTok"}]}, {})
    assert r["n_tra_loi"] == 3
    assert r["so_nguoi_khong_chon_gi"] == 1
    assert r["table"][0] == pytest.approx({"label": "Facebook", "freq": 2, "pct_nguoi": 200 / 3,
                                           "pct_luot": 200 / 3, "la_khac": False})


def test_group_comparison_matches_scipy_and_bonferroni():
    rng = np.random.default_rng(5)
    n = 300
    g = rng.choice(["Nam", "Nữ"], n)
    fb = rng.random(n) < 0.7
    tt = rng.random(n) < np.where(g == "Nữ", 0.8, 0.55)
    df = pd.DataFrame({"fb": fb.astype(int), "tt": tt.astype(int), "g": g})
    r = mr.run(df, {"dang": "nhi_phan", "nhom": "g",
                    "cot_lua_chon": [{"cot": "fb", "label": "Facebook"}, {"cot": "tt", "label": "TikTok"}]}, {})
    row = next(x for x in r["so_sanh_nhom"]["theo_lua_chon"] if x["label"] == "TikTok")
    table = pd.crosstab(df["g"], df["tt"]).to_numpy()[:, ::-1]
    chi2, p, _, _ = stats.chi2_contingency(table, correction=False)
    assert row["chi2"] == pytest.approx(chi2) and row["p"] == pytest.approx(p)
    assert row["p_bonferroni"] == pytest.approx(min(1, p * 2))
    assert row["cramers_v"] == pytest.approx(np.sqrt(chi2 / n))
    text = " ".join(ex.giai_thich(r)["bao_cao"].split())
    assert "TikTok" in text and "Bonferroni" in text


def test_small_expected_uses_fisher():
    df = pd.DataFrame({"x": [1, 0, 0, 0, 1, 1, 1, 1], "g": ["A"] * 4 + ["B"] * 4})
    r = mr.run(df, {"dang": "nhi_phan", "nhom": "g", "cot_lua_chon": [{"cot": "x", "label": "X"}]}, {})
    row = r["so_sanh_nhom"]["theo_lua_chon"][0]
    assert row["kiem_dinh"] == "Fisher's exact"
    assert row["p"] == pytest.approx(stats.fisher_exact([[1, 3], [4, 0]]).pvalue)


def test_explanation_fills_all_placeholders():
    out = ex.giai_thich(mr.run(_text_df(), {"dang": "van_ban", "cot": "kenh", "cac_lua_chon": OPTS,
                                            "label": "Kênh", "nhom": "gt"}, {}))
    text = "\n".join(out["tom_tat"] + [out["bao_cao"]] + [l for s in out["chi_tiet"] for l in s["noi_dung"]])
    assert "{" not in text and "Percent of Cases" in text and "vượt 100%" in out["bao_cao"]


def test_requires_format():
    with pytest.raises(LoiPhanTich):
        mr.run(_text_df(), {"cot": "kenh"}, {})
