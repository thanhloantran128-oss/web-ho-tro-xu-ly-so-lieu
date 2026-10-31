from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app import scales

LIB = scales.load_library(Path(__file__).resolve().parents[2] / "scales")


def _df(n_items, rows, prefix="Q"):
    return pd.DataFrame(rows, columns=[f"{prefix}{i}" for i in range(1, n_items + 1)])


def _req(ma, n, prefix="Q", **kw):
    return {"ma": ma, "cot": [f"{prefix}{i}" for i in range(1, n + 1)], **kw}


# ---------- Tính nhất quán của thư viện ----------

def test_library_loads_all_scales():
    assert len(LIB) == 17
    assert {"DASS-21", "PSS-10", "SCS-SF", "SCS-26", "BFI-10", "LIKERT"} <= set(LIB)


@pytest.mark.parametrize("ma", [m for m in LIB if m != "LIKERT"])
def test_spec_internally_consistent(ma):
    s = LIB[ma]
    n = s["so_cau"]
    assert set(s["cau_dao_nguoc"]) <= set(range(1, n + 1))
    subs = s.get("tieu_thang") or []
    if subs:
        all_items = [i for t in subs for i in t["cau"]]
        assert len(all_items) == len(set(all_items)) == n  # mỗi câu thuộc đúng một tiểu thang
    for band in (s.get("phan_loai") or []) if isinstance(s.get("phan_loai"), list) else []:
        assert band["tu"] <= band["den"]


def test_scs_reversed_items_are_negative_subscales():
    for ma in ("SCS-SF", "SCS-26"):
        s = LIB[ma]
        neg = {i for t in s["tieu_thang"] if t["ma"] in ("SJ", "IS", "OI") for i in t["cau"]}
        assert neg == set(s["cau_dao_nguoc"])


# ---------- Chấm điểm ----------

def test_pss10_reverse_items():
    df = _df(10, [[0] * 10])
    scores, rep = scales.score(df, LIB["PSS-10"], _req("PSS-10", 10))
    assert rep["trang_thai"] == "ok"
    assert scores["PSS-10_TONG"].iloc[0] == 16  # 4 câu đảo 0 → 4


def test_dass21_doubling_and_classification():
    df = _df(21, [[1] * 21] * 5)
    scores, rep = scales.score(df, LIB["DASS-21"], _req("DASS-21", 21))
    assert scores["DASS-21_D"].iloc[0] == 14
    assert "DASS-21_TONG" not in scores
    assert rep["ket_qua"]["D"]["phan_bo_muc"]["Vừa"] == pytest.approx(100)  # 14 → Vừa
    assert rep["ket_qua"]["S"]["phan_bo_muc"]["Bình thường"] == pytest.approx(100)  # 14 → Bình thường


def test_who5_multiplier():
    df = _df(5, [[3] * 5])
    scores, _ = scales.score(df, LIB["WHO-5"], _req("WHO-5", 5))
    assert scores["WHO-5_TONG"].iloc[0] == 60


def test_scs26_total_is_mean_of_subscale_means():
    s = LIB["SCS-26"]
    row = [3] * 26
    for i in next(t for t in s["tieu_thang"] if t["ma"] == "SK")["cau"]:
        row[i - 1] = 5
    scores, _ = scales.score(_df(26, [row]), s, _req("SCS-26", 26))
    assert scores["SCS-26_TONG"].iloc[0] == pytest.approx((5 + 3 * 5) / 6)  # ≠ trung bình 26 câu (3,385)


def test_scs_sf_max_self_compassion():
    s = LIB["SCS-SF"]
    row = [1 if i in s["cau_dao_nguoc"] else 5 for i in range(1, 13)]
    scores, _ = scales.score(_df(12, [row]), s, _req("SCS-SF", 12))
    assert scores["SCS-SF_TONG"].iloc[0] == 5


def test_offset_detected_then_confirmed():
    rows = [[v] * 21 for v in (1, 2, 3, 4, 2)]  # mã hóa 1–4 cho thang 0–3
    df = _df(21, rows)
    _, rep = scales.score(df, LIB["DASS-21"], _req("DASS-21", 21))
    assert rep["trang_thai"] == "can_xac_nhan"
    assert rep["kiem_tra"]["lech_ma_hoa"]["goi_y_tru"] == 1
    scores, rep = scales.score(df, LIB["DASS-21"], _req("DASS-21", 21, dich_chuyen=1))
    assert rep["trang_thai"] == "ok"
    assert scores["DASS-21_D"].iloc[0] == 0


def test_out_of_range_reports_excel_rows():
    rows = [[2] * 10, [2] * 10, [2] * 9 + [9]]
    _, rep = scales.score(_df(10, rows), LIB["PSS-10"], _req("PSS-10", 10))
    assert rep["trang_thai"] == "loi_du_lieu"
    assert rep["kiem_tra"]["ngoai_khoang"] == {"Q10": [4]}


def test_missing_item_excludes_person():
    rows = [[2] * 10, [2] * 9 + [np.nan]]
    scores, rep = scales.score(_df(10, rows), LIB["PSS-10"], _req("PSS-10", 10))
    assert scores["PSS-10_TONG"].isna().iloc[1]
    assert rep["kiem_tra"]["n_bi_loai_do_thieu"]["TONG"] == 1


def test_phq9_item9_flag_counts_only():
    rows = [[1] * 8 + [0], [1] * 8 + [2], [0] * 8 + [1]]
    _, rep = scales.score(_df(9, rows), LIB["PHQ-9"], _req("PHQ-9", 9))
    assert rep["canh_bao_rieng"]["so_nguoi_tra_loi_lon_hon_0"] == 2


def test_likert_undeclared_reverse_item_is_flagged():
    rng = np.random.default_rng(1)
    base = rng.integers(1, 6, 50)
    noise = lambda: np.clip(base + rng.integers(-1, 2, 50), 1, 5)
    df = pd.DataFrame({"TT1": noise(), "TT2": noise(), "TT3": noise(), "TT4": 6 - noise()})
    req = {"ma": "LIKERT", "gia_tri": {"min": 1, "max": 5},
           "bien": [{"ma": "TT", "cot": ["TT1", "TT2", "TT3", "TT4"], "dao": []}]}
    _, rep = scales.score(df, LIB["LIKERT"], req)
    assert "TT4" in rep["kiem_tra"]["tuong_quan_bien_tong_am"]["TT"]
    req["bien"][0]["dao"] = ["TT4"]
    scores, rep = scales.score(df, LIB["LIKERT"], req)
    assert rep["kiem_tra"]["tuong_quan_bien_tong_am"] == {}
    assert rep["kiem_tra"]["cronbach"]["TT"] > 0.7


def test_likert_band_gap_goes_to_lower_band():
    bands = LIB["LIKERT"]["phan_loai_5_muc"]
    assert scales.classify(1.805, bands) == bands[0]["muc"]
    assert scales.classify(1.81, bands) == bands[1]["muc"]
    assert scales.classify(5.0, bands) == bands[-1]["muc"]


def test_cronbach_identical_items_is_one():
    x = pd.DataFrame({"a": [1, 2, 3, 4], "b": [1, 2, 3, 4], "c": [1, 2, 3, 4]})
    assert scales.cronbach_alpha(x) == pytest.approx(1.0)


def test_unknown_scale_rejected():
    with pytest.raises(scales.LoiPhanTich):
        scales.apply_all(pd.DataFrame({"a": [1]}), LIB, [{"ma": "KHONG-CO"}])


def test_score_column_renamed_when_file_already_has_it():
    rng = np.random.default_rng(4)
    df = pd.DataFrame({f"STC{i}": rng.integers(1, 6, 30) for i in range(1, 4)})
    df["STC"] = df[["STC1", "STC2", "STC3"]].mean(axis=1)          # học sinh tự tính đúng
    df["CSVC1"], df["CSVC2"] = rng.integers(1, 6, 30), rng.integers(1, 6, 30)
    df["CSVC"] = df["CSVC1"]                                        # tự tính sai
    req = {"ma": "LIKERT", "gia_tri": {"min": 1, "max": 5},
           "bien": [{"ma": "STC", "cot": ["STC1", "STC2", "STC3"]}, {"ma": "CSVC", "cot": ["CSVC1", "CSVC2"]}]}
    out, reps = scales.apply_all(df, LIB, [req])
    assert out["STC_TB"].tolist() == pytest.approx(df["STC"].tolist())
    assert rep_ok(reps[0])
    info = reps[0]["doi_ten_cot_diem"]
    assert info["STC"]["khop"] and not info["CSVC"]["khop"]
    warns = scales.rename_warnings(reps)
    assert "khớp nhau" in warns[0] and "lệch nhau" in warns[1]
    assert reps[0]["ket_qua"]["STC"]["cot_diem"] == "STC_TB"


def rep_ok(rep):
    return rep["trang_thai"] == "ok"


def test_score_column_double_clash_is_rejected():
    df = pd.DataFrame({"A1": [1, 2], "A2": [2, 3], "A": [1, 2], "A_TB": [1, 2]})
    req = {"ma": "LIKERT", "gia_tri": {"min": 1, "max": 5}, "bien": [{"ma": "A", "cot": ["A1", "A2"]}]}
    with pytest.raises(scales.LoiPhanTich):
        scales.apply_all(df, LIB, [req])
