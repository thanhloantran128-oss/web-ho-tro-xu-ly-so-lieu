"""Kiểm thử bộ giải thích tự động: định dạng APA, chọn đúng câu mẫu, không thiếu biến điền số."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app import anova, descriptives, explain_rules as ex, scales, ttest

RNG = np.random.default_rng(3)
LIB = scales.load_library(Path(__file__).resolve().parents[2] / "scales")


def _all_text(out):
    parts = out["tom_tat"] + out["canh_bao"] + out["goi_mo"] + [out["bao_cao"]]
    for s in out["chi_tiet"]:
        parts += s["noi_dung"]
    text = "\n".join(parts)
    assert "{" not in text and "}" not in text, "còn chỗ trống chưa điền số"
    return text


# ---------- Định dạng ----------

@pytest.mark.parametrize("x, kw, expected", [
    (3.456, {}, "3,46"), (-0.5, {}, "−0,50"), (0.061, {"bo0": True}, ",06"),
    (-0.0001, {}, "0,00"), (12, {"nd": 0}, "12"),
])
def test_so(x, kw, expected):
    assert ex.so(x, **kw) == expected


def test_p_and_df_format():
    assert ex.p_txt(0.0004) == "< ,001"
    assert ex.p_txt(0.007) == "= ,007"
    assert ex.p_txt(0.35548) == "= ,355"
    assert ex.df_txt(198) == "198"
    assert ex.df_txt(170.4414) == "170,44"
    assert ex.pct(42.6) == "42,6%"


# ---------- t-test ----------

def _ind(a, b, labels=("Nam", "Nữ")):
    df = pd.DataFrame({"y": np.r_[a, b], "g": [labels[0]] * len(a) + [labels[1]] * len(b)})
    return ttest.run(df, {"type": "independent", "dv": "y", "dv_label": "niềm tin", "group": "g"}, {})


def test_ttest_significant_student():
    r = _ind(RNG.normal(3.0, 0.8, 80), RNG.normal(3.6, 0.8, 80))
    out = ex.giai_thich(r)
    text = _all_text(out)
    assert r["dong_nen_doc"] == "student"
    assert "**Nữ**" in out["tom_tat"][0] and "cao hơn" in out["tom_tat"][0]
    assert "Equal variances assumed" in text
    assert out["bao_cao"].startswith("Kết quả kiểm định Independent-samples t-test cho thấy Nữ")
    assert "Welch" not in out["bao_cao"]


def test_ttest_welch_and_not_significant():
    r = _ind(RNG.normal(3.0, 0.3, 60), RNG.normal(3.02, 1.5, 60))
    out = ex.giai_thich(r)
    text = _all_text(out)
    assert r["dong_nen_doc"] == "welch"
    assert "Chưa đủ bằng chứng" in out["tom_tat"][0]
    assert "hiệu chỉnh Welch" in out["bao_cao"]
    assert "không** có nghĩa là hai nhóm giống nhau" in text


def test_ttest_small_skewed_group_warns():
    a = np.r_[np.ones(8), 5, 5]  # lệch mạnh, nhóm nhỏ
    out = ex.giai_thich(_ind(a, RNG.normal(2, 1, 40)))
    assert "lệch đáng kể" in _all_text(out)


def test_one_sample_and_paired():
    x = RNG.normal(3.7, 0.7, 50)
    df = pd.DataFrame({"x": x, "y": x - 0.5 + RNG.normal(0, 0.3, 50)})
    out = ex.giai_thich(ttest.run(df, {"type": "one-sample", "dv": "x", "test_value": 3}, {}))
    assert "cao hơn giá trị 3" in _all_text(out)
    out = ex.giai_thich(ttest.run(df, {"type": "paired", "dv": "x", "dv2": "y", "labels": ["Trước", "Sau"]}, {}))
    assert out["tom_tat"][0].startswith("Điểm số ở **Trước**")
    df["y"] = df["x"] + RNG.normal(0, 0.3, 50)
    out = ex.giai_thich(ttest.run(df, {"type": "paired", "dv": "x", "dv2": "y", "labels": ["Trước", "Sau"]}, {}))
    assert "khác nhau giữa Trước và Sau" in out["tom_tat"][0] and "so với" not in out["tom_tat"][0]


# ---------- ANOVA ----------

def test_anova_significant_reports_pairs():
    g = [RNG.normal(3.2, 0.6, 50), RNG.normal(3.3, 0.6, 50), RNG.normal(3.9, 0.6, 50)]
    df = pd.DataFrame({"y": np.concatenate(g), "k": [10] * 50 + [11] * 50 + [12] * 50})
    out = ex.giai_thich(anova.run(df, {"dv": "y", "dv_label": "căng thẳng", "factor": "k", "factor_label": "khối"}, {}))
    text = _all_text(out)
    assert "**12**" in text and "Tukey HSD" in out["bao_cao"]
    assert "η² = ," in out["bao_cao"]


def test_anova_not_significant_no_pairs():
    g = [RNG.normal(3, 1, 40) for _ in range(3)]
    df = pd.DataFrame({"y": np.concatenate(g), "k": [1] * 40 + [2] * 40 + [3] * 40})
    r = anova.run(df, {"dv": "y", "factor": "k"}, {})
    out = ex.giai_thich(r)
    if not r["co_y_nghia_tong_the"]:
        assert "**Không** đọc bảng kiểm định sau" in _all_text(out)
        assert "Kiểm định sau" not in out["bao_cao"]


# ---------- Mô tả, tần suất, trung bình ----------

def test_descriptive_frequency_means():
    df = pd.DataFrame({"gt": ["Nam"] * 40 + ["Nữ"] * 57 + [None] * 3,
                       "khoi": [10] * 30 + [11] * 35 + [12] * 35,
                       "gio": np.r_[RNG.exponential(2, 100)],
                       "q1": RNG.integers(1, 6, 100), "q2": RNG.integers(1, 6, 100)})
    out = ex.giai_thich(descriptives.describe(df, {"variables": [
        {"name": "gt", "label": "Giới tính", "type": "nominal"},
        {"name": "gio", "label": "Giờ dùng MXH", "type": "scale"}]}, {}))
    text = _all_text(out)
    assert "Nữ" in text and "lệch" in text
    out = ex.giai_thich(descriptives.frequencies(df, {"variable": "khoi", "type": "ordinal"}, {}))
    assert "Cumulative Percent" in _all_text(out)
    out = ex.giai_thich(descriptives.frequencies(df, {"variable": "gt", "label": "Giới tính"}, {}))
    assert "Valid Percent" in _all_text(out) and "3 người không trả lời" in out["bao_cao"]
    out = ex.giai_thich(descriptives.means(df, {"variables": [{"name": "q1"}, {"name": "q2"}], "scale_points": 5,
                                                "composite": {"name": "TT", "cot": ["q1", "q2"]}}))
    assert "quy ước chia khoảng đều" in _all_text(out)


def test_multiple_response():
    df = pd.DataFrame({"fb": [1, 1, 0], "tt": [1, 0, 1]})
    out = ex.giai_thich(descriptives.frequencies(df, {"multiple_response": True,
                                                      "cot_lua_chon": [{"cot": "fb", "label": "Facebook"},
                                                                       {"cot": "tt", "label": "TikTok"}]}, {}))
    assert "tổng có thể vượt 100%" in _all_text(out)


# ---------- Thang đo ----------

def _scale_out(df, req):
    _, rep = scales.score(df, LIB[req["ma"]], req)
    return ex.giai_thich({"analysis": "thang-do", "ket_qua_thang_do": [rep]})


def test_scale_ok_sensitive():
    rows = RNG.integers(0, 4, (60, 21))
    df = pd.DataFrame(rows, columns=[f"D{i}" for i in range(1, 22)])
    out = _scale_out(df, {"ma": "DASS-21", "cot": list(df.columns)})
    text = _all_text(out)
    assert "DASS-21 – Trầm cảm" in text and "không gắn nhãn cho cá nhân" in text
    assert "Phân bố theo ngưỡng tham khảo" in text


def test_scale_needs_confirmation_and_errors():
    df = pd.DataFrame([[v] * 10 for v in (1, 2, 3, 4, 5)], columns=[f"P{i}" for i in range(1, 11)])
    out = _scale_out(df, {"ma": "PSS-10", "cot": list(df.columns)})
    assert "trừ 1" in out["tom_tat"][0]
    df.iloc[0, 0] = 9
    out = _scale_out(df, {"ma": "PSS-10", "cot": list(df.columns), "dich_chuyen": 1})
    assert "dòng 2" in _all_text(out)


def test_likert_scale_alpha_in_report():
    base = RNG.integers(1, 6, 80)
    df = pd.DataFrame({f"T{i}": np.clip(base + RNG.integers(-1, 2, 80), 1, 5) for i in range(1, 4)})
    out = _scale_out(df, {"ma": "LIKERT", "gia_tri": {"min": 1, "max": 5},
                          "bien": [{"ma": "TT", "ten": "Niềm tin", "cot": ["T1", "T2", "T3"]}]})
    assert "Cronbach's α = ," in out["bao_cao"]
