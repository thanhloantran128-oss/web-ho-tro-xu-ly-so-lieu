"""Câu hỏi nghiên cứu → kế hoạch, cỡ mẫu, nhận dạng câu hỏi tự viết; kiểm tra chất lượng phiếu và loại phiếu."""
import io
import math
import json

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app import quality, research, template
from app.main import LIBRARY, app

client = TestClient(app)

BIEN = [{"ten": "Giới tính", "kieu": "phan_loai", "nhom": ["Nam", "Nữ"]},
        {"ten": "Khối lớp", "kieu": "phan_loai", "nhom": ["10", "11", "12"]},
        {"ten": "Số giờ ngủ", "kieu": "dinh_luong", "min": 0, "max": 24},
        {"ma": "HT", "ten": "Hứng thú học tập", "kieu": "likert", "so_cau": 4},
        {"ten": "Mức căng thẳng", "kieu": "thang_chuan", "thang": "PSS-10"},
        {"ten": "Kênh thông tin", "kieu": "nhieu_lua_chon", "nhom": ["Facebook", "TikTok"]}]


def _q(*cau):
    return research.build({"doi_tuong": "học sinh", "bien": BIEN, "cau_hoi": list(cau)}, LIBRARY)["cau_hoi"]


# ---------- Cỡ mẫu: khớp giá trị chuẩn của G*Power (Cohen, 1988) ----------

def test_sample_sizes_match_reference_values():
    assert research.n_ttest_doc_lap() == 64
    assert research.n_ttest_cap() == 34
    assert research.n_anova(3) == 53
    assert research.n_chi2(1) == 88
    assert research.n_tuong_quan() in (84, 85)
    assert research.n_mo_ta() == 97


# ---------- Dạng câu hỏi + loại biến → phép phân tích ----------

@pytest.mark.parametrize("cau,phep", [
    ({"dang": "mo_ta", "x": "GioiTinh"}, "tan-suat"),
    ({"dang": "mo_ta", "x": "SoGioNgu"}, "mo-ta"),
    ({"dang": "mo_ta", "x": "HT"}, "trung-binh"),
    ({"dang": "mo_ta", "x": "MucCangThang"}, "thang-do"),
    ({"dang": "mo_ta", "x": "KenhThongTin"}, "nhieu-lua-chon"),
    ({"dang": "so_sanh", "x": "GioiTinh", "y": "HT"}, "t-test-doc-lap"),
    ({"dang": "so_sanh", "x": "KhoiLop", "y": "MucCangThang"}, "anova"),
    ({"dang": "so_sanh", "x": "GioiTinh", "y": "KhoiLop"}, "bang-cheo"),
    ({"dang": "so_sanh", "x": "GioiTinh", "y": "KenhThongTin"}, "nhieu-lua-chon-nhom"),
    ({"dang": "lien_he", "x": "SoGioNgu", "y": "HT"}, "tuong-quan"),
    ({"dang": "lien_he", "x": "GioiTinh", "y": "KhoiLop"}, "bang-cheo"),
    ({"dang": "truoc_sau", "x": "SoGioNgu", "y": "HT"}, "t-test-cap"),
])
def test_question_maps_to_analysis(cau, phep):
    q = _q(cau)[0]
    assert q["loi"] == [], q["loi"]
    assert q["phep"]["ma"] == phep
    assert q["co_mau"]["n"] > 0


def test_hypotheses_are_two_sided_and_descriptive_needs_none():
    q = _q({"dang": "so_sanh", "x": "GioiTinh", "y": "HT"})[0]
    assert q["gia_thuyet"]["h0"].startswith("Không có sự khác biệt về hứng thú học tập")
    assert "(Nam / Nữ)" in q["cau_hoi"]
    assert "khong_can" in _q({"dang": "mo_ta", "x": "HT"})[0]["gia_thuyet"]


@pytest.mark.parametrize("cau,loi", [
    ({"dang": "so_sanh", "x": "SoGioNgu", "y": "HT"}, "phân loại"),           # chia nhóm theo số đo
    ({"dang": "lien_he", "x": "GioiTinh", "y": "SoGioNgu"}, "So sánh giữa"),  # một nhóm + một số đo
    ({"dang": "truoc_sau", "x": "GioiTinh", "y": "HT"}, "cùng một biến số đo"),
    ({"dang": "so_sanh", "x": "GioiTinh", "y": "GioiTinh"}, "cùng một biến"),
    ({"dang": "so_sanh", "x": "GioiTinh"}, "đủ biến"),
])
def test_wrong_variable_kinds_are_explained(cau, loi):
    q = _q(cau)[0]
    assert q["phep"] is None and loi in " ".join(q["loi"])


def test_plan_reports_largest_sample_and_variable_errors():
    plan = {"bien": BIEN + [{"ten": "Điểm 2", "ma": "2Diem", "kieu": "dinh_luong"}, {"ma": "TT1", "ten": "X", "kieu": "likert"}],
            "cau_hoi": [{"dang": "so_sanh", "x": "GioiTinh", "y": "HT"}, {"dang": "so_sanh", "x": "KhoiLop", "y": "HT"}]}
    out = research.build(plan, LIBRARY)
    assert out["co_mau_toi_thieu"] == {"n": 159, "cau": 2}
    assert len(out["loi_bien"]) == 2      # mã bắt đầu bằng số; mã Likert kết thúc bằng số
    assert research.ma_tu_ten("Số giờ ngủ (đêm)") == "SoGioNguDem"


def test_custom_question_text_is_linted():
    q = _q({"dang": "lien_he", "x": "SoGioNgu", "y": "HT", "cau_hoi_rieng": "Ảnh hưởng của giấc ngủ đến hứng thú"})[0]
    assert q["cau_hoi"] == "Ảnh hưởng của giấc ngủ đến hứng thú"
    assert any("nhân quả" in w for w in q["canh_bao"])


@pytest.mark.parametrize("text,dang,warn", [
    ("Có sự khác biệt về mức căng thẳng giữa nam và nữ không?", "so_sanh", None),
    ("Thời gian dùng mạng xã hội có liên quan đến giờ ngủ của học sinh không?", "lien_he", None),
    ("Ảnh hưởng của mạng xã hội đến kết quả học tập", "lien_he", "nhân quả"),
    ("Mức độ căng thẳng của học sinh như thế nào? Nam hay nữ cao hơn?", "so_sanh", "hai câu hỏi"),
    ("Học sinh?", None, "quá ngắn"),
])
def test_free_text_recognition(text, dang, warn):
    r = research.nhan_dang(text)
    assert r["dang"] == dang
    if warn:
        assert any(warn in w for w in r["canh_bao"])
    else:
        assert r["canh_bao"] == []


def test_plan_goes_into_template_and_back():
    plan = {"bien": BIEN, "cau_hoi": [{"dang": "so_sanh", "x": "GioiTinh", "y": "HT"}]}
    built = research.build(plan, LIBRARY)
    cfg = built["thiet_ke_phieu"]
    assert [c["ten"] for c in cfg["cot_chung"]] == ["GioiTinh", "KhoiLop", "SoGioNgu", "KenhThongTin"]
    assert cfg["thang_do"] == ["PSS-10"] and cfg["likert"]["bien"][0]["ma"] == "HT"
    content = template.build_workbook(cfg, LIBRARY)
    cols = [c.value for c in load_workbook(io.BytesIO(content))["Dữ liệu"][1]]
    back = template.read_config(content, cols)
    assert back["hop_le"] and back["ke_hoach"]["cau_hoi"][0]["x"] == "GioiTinh"


def test_api_plan_excel_and_recognition():
    plan = {"ten_de_tai": "Giấc ngủ", "bien": BIEN, "cau_hoi": [{"dang": "lien_he", "x": "SoGioNgu", "y": "HT"}]}
    r = client.post("/ke-hoach", json=plan)
    assert r.status_code == 200 and r.json()["cau_hoi"][0]["phep"]["phan_tich"] == "tuong-quan"
    r = client.post("/ke-hoach/excel", json=plan)
    assert r.status_code == 200
    ws = load_workbook(io.BytesIO(r.content))["Kế hoạch"]
    assert ws["A1"].value == "Giấc ngủ" and "liên hệ" in ws["B5"].value
    assert client.post("/ke-hoach/excel", json={"bien": BIEN, "cau_hoi": []}).status_code == 400
    assert client.post("/cau-hoi/nhan-dang", json={"text": "Có khác biệt giữa các khối không?"}).json()["dang"] == "so_sanh"


# ---------- Chất lượng phiếu ----------

def _phieu(n=40):
    rng = np.random.default_rng(2)
    df = pd.DataFrame({"Dấu thời gian": [f"t{i}" for i in range(n)], "GioiTinh": rng.choice(["Nam", "Nữ"], n),
                       **{f"TT{i}": rng.integers(1, 6, n) for i in range(1, 7)}, "KiemTra": 4, "Diem": rng.normal(7, 1, n)})
    df.loc[3, [f"TT{i}" for i in range(1, 7)]] = 2                # chọn một đáp án cho mọi câu
    df.loc[10] = df.loc[2]
    df.loc[10, "Dấu thời gian"] = "khác giờ"                       # trùng lặp (không tính dấu thời gian)
    df.loc[12, ["GioiTinh", "TT1", "TT2", "TT3", "TT4", "TT5", "Diem"]] = np.nan   # bỏ trống quá nửa
    df.loc[[5, 6], "KiemTra"] = [2, np.nan]                        # sai câu kiểm tra chú ý
    return df


def _nhom(rep):
    return {g["ma"]: g["dong"] for g in rep["nhom"]}


def test_quality_flags_each_problem_with_excel_rows():
    rep = quality.check(_phieu(), {"chu_y": {"cot": "KiemTra", "dung": "4"}})
    g = _nhom(rep)
    assert g == {"trung_lap": [12], "mot_dap_an": [5], "bo_trong": [14], "chu_y": [7, 8]}
    assert all(x["ten"] and x["giai_thich"] for x in rep["nhom"])


def test_quality_attention_accepts_likert_text():
    df = pd.DataFrame({"Q": ["Đồng ý", "Rất đồng ý", "đồng ý ", None]})
    assert _nhom(quality.check(df, {"chu_y": {"cot": "Q", "dung": "4"}}))["chu_y"] == [3, 5]
    with pytest.raises(Exception):
        quality.check(df, {"chu_y": {"cot": "KhongCo", "dung": "4"}})


def test_few_likert_items_do_not_trigger_straight_lining():
    df = _phieu()[["GioiTinh", "TT1", "TT2", "TT3"]]
    assert _nhom(quality.check(df))["mot_dap_an"] == []


def test_exclude_keeps_original_rows_and_refuses_empty():
    df = _phieu()
    out = quality.exclude(df, [2, 5])
    assert len(out) == len(df) - 2 and 0 not in out.index and 3 not in out.index
    with pytest.raises(Exception):
        quality.exclude(df.head(1), [2])


def test_api_quality_and_excluded_rows_change_n():
    df = _phieu()
    files = lambda: {"file": ("d.csv", df.to_csv(index=False).encode(), "text/csv")}
    r = client.post("/chat-luong", files=files(), data={"params": json.dumps({"chu_y": {"cot": "KiemTra", "dung": "4"}})})
    assert r.status_code == 200 and "khác giờ" not in r.text and "Nam" not in r.text   # chỉ trả số dòng, không trả dữ liệu
    loai = sorted({d for g in r.json()["nhom"] for d in g["dong"]})
    p = {"analysis": "mo-ta", "variables": [{"name": "Diem", "type": "scale"}]}
    full = client.post("/phan-tich", files=files(), data={"params": json.dumps(p)}).json()
    cut = client.post("/phan-tich", files=files(), data={"params": json.dumps({**p, "loai_dong": loai})}).json()
    n = lambda body: body["bien"][0]["n_valid"] if "bien" in body else body["variables"][0]["n_valid"]
    assert n(full) - n(cut) == len([d for d in loai if not pd.isna(df.loc[d - 2, "Diem"])])


# ---------- Căn cứ khoa học của cỡ mẫu ----------

@pytest.mark.parametrize("muc,moi_nhom,r_n", [("nho", 394, 783), ("trung_binh", 64, 85), ("lon", 26, 30)])
def test_effect_size_level_changes_sample_size(muc, moi_nhom, r_n):
    plan = {"bien": BIEN, "muc_anh_huong": muc,
            "cau_hoi": [{"dang": "so_sanh", "x": "GioiTinh", "y": "HT"}, {"dang": "lien_he", "x": "SoGioNgu", "y": "HT"}]}
    q = research.build(plan, LIBRARY)["cau_hoi"]
    assert q[0]["co_mau"]["moi_nhom"] == moi_nhom      # Cohen (1992, Bảng 2): 393 / 64 / 26
    assert q[1]["co_mau"]["n"] == r_n                   # Cohen (1992, Bảng 2): 783 / 85 / 28 (Fisher z xấp xỉ)


def test_every_sample_size_has_method_and_source():
    cau = [{"dang": "mo_ta", "x": "HT"}, {"dang": "so_sanh", "x": "GioiTinh", "y": "HT"},
           {"dang": "so_sanh", "x": "KhoiLop", "y": "HT"}, {"dang": "so_sanh", "x": "GioiTinh", "y": "KhoiLop"},
           {"dang": "lien_he", "x": "SoGioNgu", "y": "HT"}, {"dang": "truoc_sau", "x": "SoGioNgu", "y": "HT"}]
    out = research.build({"bien": BIEN, "cau_hoi": cau}, LIBRARY)
    for q in out["cau_hoi"]:
        cc = q["co_mau"]["can_cu"]
        assert cc["cach_tinh"] and cc["nguon"]
    assert "Cohen (1992, Bảng 2) cho 64" in out["cau_hoi"][1]["co_mau"]["can_cu"]["doi_chieu"]
    assert out["cau_hoi"][3]["co_mau"]["can_cu"]["doi_chieu"] is None     # bảng 2 × 3, không có trong bảng đối chiếu
    refs = " ".join(out["can_cu_co_mau"]["tai_lieu"])
    assert "10.1037/0033-2909.112.1.155" in refs and "Sampling techniques" in refs and "G∗Power 3" in refs


def test_comparison_note_only_for_medium_effect():
    out = research.build({"bien": BIEN, "muc_anh_huong": "lon", "cau_hoi": [{"dang": "so_sanh", "x": "GioiTinh", "y": "HT"}]}, LIBRARY)
    assert out["cau_hoi"][0]["co_mau"]["can_cu"]["doi_chieu"] is None
    assert "mức ảnh hưởng lớn" in out["gia_dinh_co_mau"]


def test_finite_population_correction_for_descriptive_questions():
    assert research.n_mo_ta(0.10, 300) == math.ceil(97 / (1 + 96 / 300))
    out = research.build({"bien": BIEN, "tong_the": 300, "cau_hoi": [{"dang": "mo_ta", "x": "HT"}]}, LIBRARY)
    q = out["cau_hoi"][0]["co_mau"]
    assert q["n"] == 74 and "tổng thể 300" in q["mo_ta"]
    assert research.build({"bien": BIEN, "tong_the": "abc", "cau_hoi": []}, LIBRARY)["tong_the"] is None


def test_excel_plan_has_basis_column_and_references():
    plan = {"bien": BIEN, "cau_hoi": [{"dang": "so_sanh", "x": "GioiTinh", "y": "HT"}]}
    ws = load_workbook(io.BytesIO(client.post("/ke-hoach/excel", json=plan).content))["Kế hoạch"]
    assert ws["I4"].value == "Căn cứ cỡ mẫu" and "Cohen (1992)" in ws["I5"].value
    texts = [c.value for c in ws["A"] if isinstance(c.value, str)]
    assert "Tài liệu tham khảo" in texts and any(t.startswith("Cohen, J. (1992)") for t in texts)
