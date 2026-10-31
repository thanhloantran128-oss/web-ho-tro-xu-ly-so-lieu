import json

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import data_prep
from app.io_utils import read_table
from app.main import app
from app.utils import LoiPhanTich

client = TestClient(app)


# ---------- Đọc CSV ----------

def test_csv_semicolon_and_decimal_comma():
    content = "GioiTinh;Gio;Kenh\nNữ;3,5;\"Facebook, TikTok\"\nNam;2;Zalo\n".encode("utf-8-sig")
    df, _ = read_table("data.csv", content)
    assert list(df.columns) == ["GioiTinh", "Gio", "Kenh"]
    assert df["Gio"].tolist() == [3.5, 2.0]
    assert df["Kenh"].iloc[0] == "Facebook, TikTok"


def test_csv_comma_with_quoted_text():
    content = 'a,b\n1.5,"x, y"\n2,z\n'.encode("utf-8")
    df, _ = read_table("data.csv", content)
    assert df["a"].tolist() == [1.5, 2.0] and df["b"].iloc[0] == "x, y"


def test_text_is_nfc_normalized_and_stripped():
    import unicodedata
    decomposed = unicodedata.normalize("NFD", "Đồng ý")
    df, _ = read_table("data.csv", f"q\n {decomposed} \nKhông đồng ý\n".encode("utf-8"))
    assert df["q"].iloc[0] == "Đồng ý"


def test_template_workbook_reads_data_sheet_and_drops_empty_rows():
    from io import BytesIO
    from pathlib import Path

    from openpyxl import load_workbook

    path = Path(__file__).resolve().parents[2] / "mau-nhap-lieu" / "mau-nhap-lieu.xlsx"
    wb = load_workbook(path)
    ws = wb["Dữ liệu"]
    ws.append([])  # dòng 2 để trống
    for row in (["Nữ", 10, 3.5, 4, 4, 5, 2, "Facebook, TikTok"], ["Nam", 12, 2, 3, 3, 4, 3, "TikTok"]):
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    df, _ = read_table("mau.xlsx", buf.getvalue())
    assert len(df) == 2 and df["GioiTinh"].tolist() == ["Nữ", "Nam"]


# ---------- Đổi chữ sang số ----------

def _likert_text():
    return pd.DataFrame({
        "TT1": ["Đồng ý", "Rất đồng ý", "rất không đồng ý ", "Trung lập", None],
        "TT2": ["Không đồng ý", "Đồng ý", "Đồng ý", "Rất đồng ý", "Đồng ý"],
        "F1": ["Không bao giờ", "Thỉnh thoảng", "Rất thường xuyên", "Hiếm khi", "Thường xuyên"],
        "GioiTinh": ["Nam", "Nữ", "Nữ", "Nam", "Nữ"],
    })


def test_suggest_recode_groups_columns_by_label_set():
    groups = {g["bo"]: g for g in data_prep.suggest_recode(_likert_text())}
    assert groups["dong_y_5"]["cot"] == ["TT1", "TT2"] and groups["dong_y_5"]["khop_hoan_toan"]
    assert groups["tan_suat_5"]["cot"] == ["F1"]
    assert all("GioiTinh" not in g["cot"] for g in groups.values())


def test_apply_recode_builtin_and_custom():
    df = data_prep.apply_recode(_likert_text(), [{"cot": ["TT1", "TT2"], "bo": "dong_y_5"}])
    assert df["TT1"].tolist()[:4] == [4, 5, 1, 3] and np.isnan(df["TT1"].iloc[4])
    df = data_prep.apply_recode(_likert_text(), [{"cot": ["GioiTinh"], "bang": {"Nam": 1, "Nữ": 2}}])
    assert df["GioiTinh"].tolist() == [1, 2, 2, 1, 2]


def test_apply_recode_rejects_unmapped_values():
    df = pd.DataFrame({"q": ["Đồng ý", "Hơi đồng ý"]})
    with pytest.raises(LoiPhanTich, match="Hơi đồng ý"):
        data_prep.apply_recode(df, [{"cot": ["q"], "bo": "dong_y_5"}])


def test_partial_match_lists_unknown_labels():
    df = pd.DataFrame({"q": ["Đồng ý", "Rất đồng ý", "Hơi đồng ý", "Không đồng ý"]})
    g = data_prep.suggest_recode(df)[0]
    assert not g["khop_hoan_toan"] and g["gia_tri_chua_khop"] == ["hơi đồng ý"]


# ---------- Mã thiếu ----------

def test_missing_code_detected_and_applied():
    df = pd.DataFrame({"q1": [1, 2, 99, 5, 3], "tuoi": [15, 16, 99, 17, 16], "diem": [120, 99, 150, 80, 110]})
    warns = {w["cot"]: w for w in data_prep.missing_code_warnings(df)}
    assert warns["q1"]["gia_tri"] == [99] and warns["q1"]["dong"] == [4]
    assert "tuoi" in warns and "diem" not in warns  # 99 là điểm hợp lệ khi các giá trị khác cũng lớn
    out = data_prep.apply_missing_codes(df, [99])
    assert out["q1"].isna().sum() == 1


# ---------- Qua API ----------

def _csv(df):
    return df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


def test_preview_suggests_recode_and_scale_after_recode():
    rng = np.random.default_rng(0)
    labels = ["Không bao giờ", "Hầu như không", "Thỉnh thoảng", "Khá thường xuyên", "Rất thường xuyên"]
    df = pd.DataFrame({f"PSS{i}": rng.choice(labels, 30) for i in range(1, 11)})
    body = client.post("/xem-truoc", files={"file": ("d.csv", _csv(df), "text/csv")}).json()
    assert body["goi_y_ma_hoa_chu"][0]["bo"] == "tan_suat_5"
    group = body["goi_y_thang_do"][0]
    # Sau khi đổi chữ thành 1–5, PSS-10 (0–4) được nhận ra kèm lệch mã hóa 1
    top = group["thang_co_the"][0]
    assert (top["ma"], top["lech_ma_hoa"], top["khop_ten"]) == ("PSS-10", 1, True)


def test_analysis_with_recode_missing_codes_and_warnings():
    df = pd.DataFrame({"q": ["Đồng ý", "Rất đồng ý", "Không đồng ý", "Đồng ý"], "tuoi": [15, 99, 16, 17],
                       "g": ["Nam", "Nữ", "Nam", "Nữ"]})
    files = {"file": ("d.csv", _csv(df), "text/csv")}
    params = {"analysis": "trung-binh", "variables": [{"name": "q"}], "ma_hoa_chu": [{"cot": ["q"], "bo": "dong_y_5"}]}
    r = client.post("/phan-tich", files=files, data={"params": json.dumps(params)}).json()
    assert r["variables"][0]["mean"] == pytest.approx(3.75)  # (4 + 5 + 2 + 4) / 4
    assert any("tuoi" in w for w in r["canh_bao_du_lieu"])
    assert r["giai_thich"]["canh_bao"][0] == r["canh_bao_du_lieu"][0]
    params["ma_thieu"] = [99]
    files = {"file": ("d.csv", _csv(df), "text/csv")}
    r = client.post("/phan-tich", files=files, data={"params": json.dumps(params)}).json()
    assert r["canh_bao_du_lieu"] == []
