"""Ràng buộc t-test / ANOVA theo loại thang đo."""
import json

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import assumptions
from app.main import app
from app.utils import LoiPhanTich

client = TestClient(app)
RNG = np.random.default_rng(8)
N = 90


def _df():
    return pd.DataFrame({
        "GioiTinh": RNG.choice(["Nam", "Nữ"], N),
        "Khoi": RNG.choice([10, 11, 12], N),
        "Lop": RNG.choice(["10A1", "10A2", "11A1"], N),
        "GioMXH": RNG.normal(3, 1.2, N).round(1),
        "Diem": RNG.normal(7, 1, N).round(2),
        "CoDiLam": RNG.choice([0, 1], N),
        "Q1": RNG.integers(1, 6, N),
        "Q2": RNG.integers(1, 6, N),
    })


def _ttest(**kw):
    return {"type": "independent", "dv": "Diem", "group": "GioiTinh", **kw}


def test_valid_numeric_dv_passes():
    assert assumptions.check_before("t-test", _df(), _ttest(), []) == []
    assert assumptions.check_before("anova", _df(), {"dv": "Diem", "factor": "Khoi"}, []) == []


@pytest.mark.parametrize("dv, phrase", [("Lop", "định danh"), ("CoDiLam", "nhị phân")])
def test_nominal_or_binary_dv_blocked(dv, phrase):
    with pytest.raises(LoiPhanTich, match=phrase):
        assumptions.check_before("t-test", _df(), _ttest(dv=dv), [])


def test_constant_dv_blocked():
    df = _df().assign(Diem=5)
    with pytest.raises(LoiPhanTich, match="một giá trị duy nhất"):
        assumptions.check_before("anova", df, {"dv": "Diem", "factor": "Khoi"}, [])


def test_continuous_grouping_variable_blocked():
    with pytest.raises(LoiPhanTich, match="số đo liên tục"):
        assumptions.check_before("anova", _df(), {"dv": "Diem", "factor": "GioMXH"}, [])


def test_same_column_blocked():
    with pytest.raises(LoiPhanTich, match="cùng một cột"):
        assumptions.check_before("anova", _df(), {"dv": "Khoi", "factor": "Khoi"}, [])
    with pytest.raises(LoiPhanTich, match="cùng một cột"):
        assumptions.check_before("t-test", _df(), {"type": "paired", "dv": "Q1", "dv2": "Q1"}, [])


def test_single_likert_item_warns_with_nonparametric_p():
    pending = assumptions.check_before("t-test", _df(), _ttest(dv="Q1"), [])
    msgs = assumptions.finish(pending, {"analysis": "t-test", "type": "independent", "groups": [],
                                        "nonparametric": {"test": "Mann-Whitney U", "p": 0.0312}})
    assert "một câu Likert đơn lẻ" in msgs[0] and "Mann-Whitney U (*p* = ,031)" in msgs[0]


def test_scale_score_column_not_flagged_but_low_alpha_warned():
    reps = [{"ket_qua": {"TT": {"cot_diem": "Q1"}}, "kiem_tra": {"cronbach": {"TT": 0.42}}}]
    pending = assumptions.check_before("t-test", _df(), _ttest(dv="Q1"), reps)
    msgs = assumptions.finish(pending, {"analysis": "anova"})
    assert len(msgs) == 1 and "Cronbach's α = ,42" in msgs[0]


def test_paired_different_scales_and_one_sample_out_of_range():
    df = _df().assign(Truoc=RNG.integers(1, 6, N), Sau=RNG.integers(0, 101, N))
    w = assumptions.finish(assumptions.check_before("t-test", df, {"type": "paired", "dv": "Truoc", "dv2": "Sau"}, []), {})
    assert any("không cùng một thang" in m for m in w)
    w = assumptions.finish(assumptions.check_before("t-test", df, {"type": "one-sample", "dv": "Diem", "test_value": 30}, []), {})
    assert any("nằm ngoài khoảng" in m for m in w)


def test_api_returns_explanation_instead_of_running():
    df = _df()
    params = {"analysis": "anova", "dv": "Lop", "factor": "Khoi"}
    r = client.post("/phan-tich", files={"file": ("d.csv", df.to_csv(index=False).encode(), "text/csv")},
                    data={"params": json.dumps(params)})
    assert r.status_code == 400 and "biến phụ thuộc phải là biến **định lượng**" in r.json()["detail"]


def test_api_warnings_appear_first_in_explanation():
    df = _df()
    params = {"analysis": "t-test", "type": "independent", "dv": "Q1", "group": "GioiTinh"}
    r = client.post("/phan-tich", files={"file": ("d.csv", df.to_csv(index=False).encode(), "text/csv")},
                    data={"params": json.dumps(params)}).json()
    assert "một câu Likert đơn lẻ" in r["giai_thich"]["canh_bao"][0]
    assert any("mỗi người chỉ thuộc **một** nhóm" in m for m in r["kiem_tra_dieu_kien"])
