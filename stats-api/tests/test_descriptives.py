import numpy as np
import pandas as pd
import pytest
from scipy import stats

from app import descriptives


def test_frequencies_valid_percent_and_missing():
    df = pd.DataFrame({"g": [1, 1, 2, 2, 2, np.nan]})
    r = descriptives.frequencies(df, {"variable": "g", "type": "nominal"}, {"g": {1.0: "Nam", 2.0: "Nữ"}})
    assert r["n_valid"] == 5 and r["n_missing"] == 1
    nu = r["table"][1]
    assert nu["label"] == "Nữ"
    assert nu["percent"] == pytest.approx(50.0)
    assert nu["valid_percent"] == pytest.approx(60.0)
    assert nu["cum_percent"] is None  # biến định danh không có % tích lũy


def test_cumulative_percent_for_ordinal():
    df = pd.DataFrame({"k": [10, 10, 11, 12]})
    r = descriptives.frequencies(df, {"variable": "k", "type": "ordinal"}, {})
    assert [row["cum_percent"] for row in r["table"]] == pytest.approx([50, 75, 100])


def test_multiple_response_percent_of_respondents():
    df = pd.DataFrame({"fb": [1, 1, 0, np.nan], "tt": [1, 0, 1, np.nan]})
    r = descriptives.frequencies(df, {"multiple_response": True,
                                      "cot_lua_chon": [{"cot": "fb"}, {"cot": "tt"}]}, {})
    assert r["n_valid"] == 3
    assert sum(row["percent"] for row in r["table"]) == pytest.approx(400 / 3)


def test_summary_matches_spss_formulas():
    x = pd.Series([1, 2, 2, 3, 3, 3, 4, 5, 5, 9])
    s = descriptives.summary_numeric(x)
    assert s["sd"] == pytest.approx(np.std(x, ddof=1))
    assert s["se"] == pytest.approx(np.std(x, ddof=1) / np.sqrt(10))
    assert s["skewness"] == pytest.approx(stats.skew(x, bias=False))
    assert s["kurtosis"] == pytest.approx(stats.kurtosis(x, bias=False))


def test_composite_listwise():
    df = pd.DataFrame({"a": [4, 5, np.nan], "b": [2, 3, 4]})
    r = descriptives.means(df, {"variables": [], "composite": {"name": "TT", "cot": ["a", "b"]}})
    assert r["composite"]["n"] == 2
    assert r["composite"]["mean"] == pytest.approx(3.5)
    assert r["composite"]["n_bi_loai_do_thieu"] == 1


# ---------- Thứ tự nhóm của biến thứ bậc dạng chữ ----------

def test_known_vietnamese_order_for_cumulative_percent():
    df = pd.DataFrame({"hl": ["Giỏi"] * 3 + ["Khá"] * 4 + ["Trung bình"] * 2 + ["Xuất sắc"]})
    r = descriptives.frequencies(df, {"variable": "hl", "type": "ordinal"}, {})
    assert [row["label"] for row in r["table"]] == ["Trung bình", "Khá", "Giỏi", "Xuất sắc"]
    assert [row["cum_percent"] for row in r["table"]] == pytest.approx([20, 60, 90, 100])
    assert r["nguon_thu_tu"] == "tu_nhan"


def test_user_order_overrides_and_unknown_labels_go_last():
    df = pd.DataFrame({"m": ["Dưới 5", "5 – 6,4", "Từ 8", "6,5 – 7,9", "Từ 8", "Khác"]})
    order = ["Dưới 5", "5 – 6,4", "6,5 – 7,9", "Từ 8"]
    r = descriptives.frequencies(df, {"variable": "m", "type": "ordinal", "thu_tu": order}, {})
    assert [row["label"] for row in r["table"]] == order + ["Khác"]
    assert r["nguon_thu_tu"] == "nguoi_dung"
    out = descriptives.describe(df, {"variables": [{"name": "m", "type": "ordinal", "thu_tu": order}]}, {})
    assert [row["label"] for row in out["variables"][0]["tan_suat"]][:4] == order


def test_preview_lists_categories_and_guesses_ordinal():
    from pathlib import Path

    from app.io_utils import preview
    from app.scales import load_library

    df = pd.DataFrame({"hl": ["Khá", "Giỏi", "Trung bình"], "lop": ["10A1", "10A2", "10A1"]})
    cols = {c["name"]: c for c in preview(df, load_library(Path(__file__).resolve().parents[2] / "scales"))["cot"]}
    assert cols["hl"]["kieu_goi_y"] == "ordinal" and cols["hl"]["cac_gia_tri"] == ["Trung bình", "Khá", "Giỏi"]
    assert cols["lop"]["kieu_goi_y"] == "nominal" and not cols["lop"]["thu_tu_tu_nhan"]
