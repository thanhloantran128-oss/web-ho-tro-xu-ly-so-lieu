import json

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from scipy import stats

from app import assumptions, correlation, crosstab
from app import explain_rules as ex
from app.main import app
from app.utils import LoiPhanTich

client = TestClient(app)
RNG = np.random.default_rng(21)


def _text(out):
    parts = out["tom_tat"] + out["canh_bao"] + out["goi_mo"] + [out["bao_cao"]]
    parts += [l for s in out["chi_tiet"] for l in s["noi_dung"]]
    text = "\n".join(parts)
    assert "{" not in text and "}" not in text
    return text


# ---------- Bảng chéo ----------

def _cross_df(n=300):
    g = RNG.choice(["Nam", "Nữ"], n)
    nt = np.where(RNG.random(n) < np.where(g == "Nữ", 0.65, 0.4), "TikTok", "Facebook")
    hl = RNG.choice(["Khá", "Giỏi", "Trung bình"], n)
    return pd.DataFrame({"GioiTinh": g, "NenTang": nt, "HocLuc": hl})


def test_crosstab_matches_scipy_and_orders_known_levels():
    df = _cross_df()
    r = crosstab.run(df, {"hang": "HocLuc", "cot": "NenTang"}, {})
    assert r["hang"]["nhom"] == ["Trung bình", "Khá", "Giỏi"]
    obs = pd.crosstab(df["HocLuc"], df["NenTang"]).reindex(["Trung bình", "Khá", "Giỏi"]).to_numpy()
    chi2, p, dof, _ = stats.chi2_contingency(obs, correction=False)
    assert r["chi2"] == pytest.approx(chi2) and r["p"] == pytest.approx(p) and r["df"] == dof
    assert r["cramers_v"] == pytest.approx(np.sqrt(chi2 / (obs.sum() * 1)))
    assert all(sum(row) == pytest.approx(100) for row in r["pct_hang"])


def test_crosstab_significant_explanation():
    r = crosstab.run(_cross_df(), {"hang": "GioiTinh", "cot": "NenTang", "hang_label": "giới tính",
                                   "cot_label": "nền tảng chính"}, {})
    out = ex.giai_thich(r)
    text = _text(out)
    assert r["p"] < 0.05 and "Có liên hệ có ý nghĩa thống kê" in out["tom_tat"][0]
    assert "χ²(1, *N* = 300)" in out["bao_cao"] and "Cramér's V = ," in out["bao_cao"]
    assert "nhóm Nữ" in out["bao_cao"]


def test_crosstab_small_2x2_uses_fisher():
    df = pd.DataFrame({"a": ["x"] * 6 + ["y"] * 6, "b": ["u", "u", "u", "u", "u", "v", "u", "v", "v", "v", "v", "v"]})
    r = crosstab.run(df, {"hang": "a", "cot": "b"}, {})
    assert r["kiem_dinh_nen_doc"] == "fisher"
    assert r["fisher_p"] == pytest.approx(stats.fisher_exact([[5, 1], [1, 5]]).pvalue)
    assert "Fisher" in ex.giai_thich(r)["bao_cao"]


def test_crosstab_constraints():
    df = _cross_df().assign(Diem=RNG.normal(7, 1, 300).round(2))
    with pytest.raises(LoiPhanTich, match="số đo liên tục"):
        assumptions.check_before("bang-cheo", df, {"hang": "GioiTinh", "cot": "Diem"}, [])
    with pytest.raises(LoiPhanTich, match="cùng một cột"):
        assumptions.check_before("bang-cheo", df, {"hang": "GioiTinh", "cot": "GioiTinh"}, [])


# ---------- Tương quan ----------

def _corr_df(n=150):
    x = RNG.normal(3, 1, n)
    return pd.DataFrame({"Gio": x.round(2), "CangThang": (20 + 4 * x + RNG.normal(0, 5, n)).round(2),
                         "Diem": RNG.normal(7, 1, n).round(2), "Q1": RNG.integers(1, 6, n),
                         "Lop": RNG.choice(["10A1", "10A2"], n), "CoDiLam": RNG.choice([0, 1], n)})


@pytest.mark.parametrize("method, fn", [("pearson", stats.pearsonr), ("spearman", stats.spearmanr)])
def test_correlation_matches_scipy(method, fn):
    df = _corr_df()
    r = correlation.run(df, {"bien": ["Gio", "CangThang", "Diem"], "phuong_phap": method}, {})
    pair = next(c for c in r["cap"] if {c["x"], c["y"]} == {"Gio", "CangThang"})
    ref = fn(df["Gio"], df["CangThang"])
    assert pair["r"] == pytest.approx(ref.statistic) and pair["p"] == pytest.approx(ref.pvalue)
    assert pair["df"] == len(df) - 2 and r["so_cap_kiem_dinh"] == 3
    assert pair["p_bonferroni"] == pytest.approx(min(1, ref.pvalue * 3))


def test_correlation_pairwise_missing_and_ci():
    df = _corr_df()
    df.loc[:9, "Diem"] = np.nan
    r = correlation.run(df, {"bien": ["Gio", "Diem"], "phuong_phap": "pearson"}, {})
    c = r["cap"][0]
    assert c["n"] == len(df) - 10 and c["ci95"][0] < c["r"] < c["ci95"][1]


def test_correlation_explanation_apa():
    df = _corr_df()
    r = correlation.run(df, {"bien": ["Gio", "CangThang"], "nhan": {"Gio": "giờ dùng MXH", "CangThang": "mức căng thẳng"}}, {})
    out = ex.giai_thich(r)
    _text(out)
    assert out["bao_cao"].startswith("Kết quả phân tích tương quan Pearson cho thấy giờ dùng MXH và mức căng thẳng")
    assert "*r*(148) = ," in out["bao_cao"]
    assert any("không phải nhân quả" in w for w in out["canh_bao"])


def test_correlation_constraints():
    df = _corr_df()
    with pytest.raises(LoiPhanTich, match="định danh"):
        assumptions.check_before("tuong-quan", df, {"bien": ["Gio", "Lop"]}, [])
    with pytest.raises(LoiPhanTich, match="ít nhất 2"):
        assumptions.check_before("tuong-quan", df, {"bien": ["Gio"]}, [])
    w = assumptions.check_before("tuong-quan", df, {"bien": ["Gio", "Q1", "CoDiLam"], "phuong_phap": "pearson"}, [])
    text = " ".join(x if isinstance(x, str) else x[0] for x in w)
    assert "Spearman" in text and "nhị phân" in text
    assert assumptions.check_before("tuong-quan", df, {"bien": ["Gio", "Q1"], "phuong_phap": "spearman"}, []) == []


def test_api_end_to_end():
    df = _corr_df()
    for params in ({"analysis": "tuong-quan", "bien": ["Gio", "CangThang", "Diem"], "phuong_phap": "pearson"},
                   {"analysis": "bang-cheo", "hang": "Lop", "cot": "CoDiLam"}):
        r = client.post("/phan-tich", files={"file": ("d.csv", df.to_csv(index=False).encode(), "text/csv")},
                        data={"params": json.dumps(params)})
        assert r.status_code == 200, r.text
        assert r.json()["giai_thich"]["tom_tat"]
