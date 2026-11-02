"""Bảng α nếu loại câu, ghi chú tiêu chí độ tin cậy và nhãn giá trị do học sinh điền."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import data_prep, scales
from app.main import app

LIB = scales.load_library(Path(__file__).resolve().parents[2] / "scales")
client = TestClient(app)


def _likert(n=80, seed=3):
    """3 câu cùng đo một khái niệm + 1 câu nhiễu (không liên quan)."""
    rng = np.random.default_rng(seed)
    base = rng.integers(1, 6, n)
    near = lambda: np.clip(base + rng.integers(-1, 2, n), 1, 5)
    return pd.DataFrame({"TT1": near(), "TT2": near(), "TT3": near(), "TT4": rng.integers(1, 6, n)})


REQ = {"ma": "LIKERT", "gia_tri": {"min": 1, "max": 5},
       "bien": [{"ma": "TT", "cot": ["TT1", "TT2", "TT3", "TT4"], "dao": []}]}


# ---------- Item-Total Statistics ----------

def test_item_total_statistics_matches_definitions():
    df = _likert()
    rows = scales.item_total_statistics(df)
    assert [r["cot"] for r in rows] == list(df.columns)
    for r in rows:
        rest = df.drop(columns=r["cot"])
        assert r["alpha_neu_loai"] == pytest.approx(scales.cronbach_alpha(rest))
        assert r["mean_neu_loai"] == pytest.approx(rest.sum(axis=1).mean())
        assert r["var_neu_loai"] == pytest.approx(rest.sum(axis=1).var(ddof=1))
        assert r["tuong_quan_bien_tong"] == pytest.approx(np.corrcoef(df[r["cot"]], rest.sum(axis=1))[0, 1])


def test_alpha_if_deleted_flags_noise_item():
    df = _likert()
    alpha = scales.cronbach_alpha(df)
    rows = {r["cot"]: r for r in scales.item_total_statistics(df)}
    assert rows["TT4"]["alpha_neu_loai"] > alpha            # bỏ câu nhiễu thì α tăng
    assert rows["TT4"]["tuong_quan_bien_tong"] < 0.3
    assert rows["TT1"]["alpha_neu_loai"] < alpha


def test_item_total_statistics_listwise_and_needs_three_items():
    df = _likert()
    df.loc[0, "TT2"] = np.nan
    rows = scales.item_total_statistics(df)
    full = df.dropna()
    assert rows[0]["mean_neu_loai"] == pytest.approx(full.drop(columns="TT1").sum(axis=1).mean())
    assert scales.item_total_statistics(df[["TT1", "TT2"]]) == []


def test_score_report_contains_item_statistics_after_reversing():
    df = _likert()
    df["TT3"] = 6 - df["TT3"]                                # câu đảo chiều
    req = {**REQ, "bien": [{**REQ["bien"][0], "dao": ["TT3"]}]}
    _, rep = scales.score(df, LIB["LIKERT"], req)
    rows = rep["kiem_tra"]["thong_ke_cau"]["TT"]
    assert len(rows) == 4
    tt3 = next(r for r in rows if r["cot"] == "TT3")
    assert tt3["tuong_quan_bien_tong"] > 0.3                 # đã đảo trước khi tính


def test_api_scale_result_has_item_table_explanation_and_criteria_note():
    files = {"file": ("d.csv", _likert().to_csv(index=False).encode(), "text/csv")}
    r = client.post("/phan-tich", files=files, data={"params": json.dumps({"analysis": "thang-do", "thang_do": [REQ]})})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ket_qua_thang_do"][0]["kiem_tra"]["thong_ke_cau"]["TT"]
    notes = " ".join(body["ghi_chu_do_tin_cay"])
    assert "Cronbach's α" in notes and ",30" in notes and "nếu loại câu" in notes
    detail = " ".join(s for sec in body["giai_thich"]["chi_tiet"] for s in sec["noi_dung"])
    assert "nếu loại câu TT4" in detail


# ---------- Nhãn giá trị ----------

def test_merge_value_labels_user_overrides_spss_and_skips_unknown_columns():
    df = pd.DataFrame({"GioiTinh": [1, 2, 1]})
    out = data_prep.merge_value_labels({"GioiTinh": {1.0: "male", 2.0: "female"}},
                                       {"GioiTinh": {"1": " Nam ", "2": ""}, "KhongCo": {"1": "x"}}, df)
    assert out["GioiTinh"] == {2.0: "female", "1": "Nam"}
    assert "KhongCo" not in out
    assert data_prep.merge_value_labels({}, None, df) == {}


def test_preview_lists_numeric_codes_for_labelling():
    df = pd.DataFrame({"GioiTinh": [1, 2, 1, 2], "Diem": [6.5, 7.25, 8.0, 9.1]})
    r = client.post("/xem-truoc", files={"file": ("d.csv", df.to_csv(index=False).encode(), "text/csv")})
    cols = {c["name"]: c for c in r.json()["cot"]}
    assert cols["GioiTinh"]["gia_tri_so"] == [1, 2]
    assert cols["Diem"]["gia_tri_so"] == [6.5, 7.25, 8.0, 9.1]   # ít giá trị nên vẫn liệt kê


def _coded(n=60):
    rng = np.random.default_rng(5)
    return pd.DataFrame({"GioiTinh": rng.choice([1, 2], n), "Khoi": rng.choice([10, 11, 12], n),
                         "Diem": rng.normal(7, 1, n).round(2)})


def _run(params):
    files = {"file": ("d.csv", _coded().to_csv(index=False).encode(), "text/csv")}
    r = client.post("/phan-tich", files=files, data={"params": json.dumps(params)})
    assert r.status_code == 200, r.text
    return r.json()


def test_value_labels_show_in_crosstab_and_ttest():
    nhan = {"GioiTinh": {"1": "Nam", "2": "Nữ"}}
    body = _run({"analysis": "bang-cheo", "hang": "GioiTinh", "cot": "Khoi", "nhan_gia_tri": nhan})
    assert body["hang"]["nhom"] == ["Nam", "Nữ"]
    body = _run({"analysis": "t-test", "type": "independent", "dv": "Diem", "group": "GioiTinh", "nhan_gia_tri": nhan})
    assert [g["label"] for g in body["groups"]] == ["Nam", "Nữ"]


def test_ttest_groups_can_be_typed_as_labels():
    nhan = {"Khoi": {"10": "Khối 10", "11": "Khối 11", "12": "Khối 12"}}
    body = _run({"analysis": "t-test", "type": "independent", "dv": "Diem", "group": "Khoi",
                 "nhom": ["Khối 12", "10"], "nhan_gia_tri": nhan})
    assert [g["label"] for g in body["groups"]] == ["Khối 12", "Khối 10"]
    assert sum(g["n"] for g in body["groups"]) == int(_coded()["Khoi"].isin([10, 12]).sum())


def test_without_labels_codes_are_kept():
    body = _run({"analysis": "bang-cheo", "hang": "GioiTinh", "cot": "Khoi"})
    assert body["hang"]["nhom"] == ["1", "2"]
