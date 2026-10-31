"""A: file mẫu theo thang · B: nhận dạng tên cột Google Forms · C: bảng ghép câu – cột."""
import json
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app import scales, template
from app.io_utils import group_columns, suggest_scales
from app.main import app
from app.utils import LoiPhanTich

client = TestClient(app)
LIB = scales.load_library(Path(__file__).resolve().parents[2] / "scales")
RNG = np.random.default_rng(11)
CHUNG = [{"ten": "GioiTinh", "loai": "nhom", "lua_chon": ["Nam", "Nữ"]},
         {"ten": "Kenh", "loai": "nhieu_lua_chon", "lua_chon": ["Facebook", "TikTok"]}]


def _pss_items(n=80):
    """Dữ liệu PSS-10 hợp lý: 4 câu tích cực (4, 5, 7, 8) trả lời ngược chiều căng thẳng."""
    stress = RNG.normal(0, 1, n)
    out = {}
    for i in range(1, 11):
        raw = np.clip(np.round(2 + stress + RNG.normal(0, 0.6, n)), 0, 4).astype(int)
        out[i] = 4 - raw if i in (4, 5, 7, 8) else raw
    return out


def _fill(xlsx: bytes, rows: list[list]) -> bytes:
    wb = load_workbook(BytesIO(xlsx))
    ws = wb["Dữ liệu"]
    for r, row in enumerate(rows, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _post_preview(content: bytes, name="du-lieu.xlsx"):
    return client.post("/xem-truoc", files={"file": (name, content, "application/octet-stream")}).json()


# ---------- A. File mẫu ----------

def test_template_without_specialised_scales_needs_no_scale_info():
    cfg = {"cot_chung": CHUNG, "likert": {"so_muc": 7, "bien": [{"ma": "TT", "ten": "Niềm tin", "so_cau": 3,
                                                                   "dao": [3]}]}}
    r = client.post("/mau-nhap-lieu", json=cfg)
    assert r.status_code == 200
    wb = load_workbook(BytesIO(r.content))
    assert wb.sheetnames[0] == "Dữ liệu" and wb["_cau_hinh"].sheet_state == "hidden"
    assert [c.value for c in wb["Dữ liệu"][1]] == ["GioiTinh", "Kenh", "TT1", "TT2", "TT3"]

    rows = [["Nữ", "Facebook, TikTok", 6, 5, 2], ["Nam", "TikTok", 3, 4, 5], ["Nữ", "Facebook", 7, 6, 1],
            ["Nam", "TikTok", 2, 3, 6], ["Nữ", "Facebook", 5, 5, 3]]
    body = _post_preview(_fill(r.content, rows))
    cfg_up = body["cau_hinh_tu_file_mau"]
    assert cfg_up["hop_le"]
    likert = cfg_up["thang_do"][0]
    assert likert["ma"] == "LIKERT" and likert["gia_tri"] == {"min": 1, "max": 7}
    assert likert["bien"][0]["dao"] == ["TT3"]
    assert [row["dao_chieu"] for row in likert["bang_ghep"]] == [False, False, True]
    assert cfg_up["nhieu_lua_chon"][0]["cac_lua_chon"] == ["Facebook", "TikTok"]

    # Dùng thẳng cấu hình đọc được để phân tích, không cần khai báo gì thêm
    params = {"analysis": "trung-binh", "variables": [{"name": "TT"}], "scale_points": 7,
              "thang_do": [{k: v for k, v in likert.items() if k != "bang_ghep"}]}
    res = client.post("/phan-tich", files={"file": ("d.xlsx", _fill(r.content, rows), "application/octet-stream")},
                      data={"params": json.dumps(params)}).json()
    assert res["variables"][0]["mean"] == pytest.approx(np.mean([(6 + 5 + 6) / 3, (3 + 4 + 3) / 3, (7 + 6 + 7) / 3,
                                                                 (2 + 3 + 2) / 3, (5 + 5 + 5) / 3]))


def test_template_with_specialised_scales_is_recognised_exactly():
    r = client.post("/mau-nhap-lieu", json={"cot_chung": CHUNG[:1], "thang_do": ["PSS-10", "DASS-21"]})
    wb = load_workbook(BytesIO(r.content))
    header = [c.value for c in wb["Dữ liệu"][1]]
    assert header[1:3] == ["PSS10_1", "PSS10_2"] and header[-1] == "DASS21_21"
    items = _pss_items(20)
    rows = [["Nam"] + [int(items[i][k]) for i in range(1, 11)] + [int(RNG.integers(0, 4)) for _ in range(21)]
            for k in range(20)]
    body = _post_preview(_fill(r.content, rows))
    assert [s["ma"] for s in body["cau_hinh_tu_file_mau"]["thang_do"]] == ["PSS-10", "DASS-21"]
    pss = next(g for g in body["goi_y_thang_do"] if g["tien_to"] == "pss10")
    assert pss["thang_co_the"][0]["ma"] == "PSS-10" and pss["thang_co_the"][0]["khop_chinh_xac"]


def test_renamed_column_disables_auto_config():
    r = client.post("/mau-nhap-lieu", json={"thang_do": ["PSS-10"]})
    wb = load_workbook(BytesIO(r.content))
    wb["Dữ liệu"]["A1"] = "CauMot"
    buf = BytesIO()
    wb.save(buf)
    cfg = _post_preview(buf.getvalue())["cau_hinh_tu_file_mau"]
    assert cfg["hop_le"] is False and "PSS10_1" in cfg["cot_bi_thieu"]


@pytest.mark.parametrize("cfg", [
    {"cot_chung": [{"ten": "A", "loai": "so"}, {"ten": "a", "loai": "so"}]},
    {"likert": {"so_muc": 5, "bien": [{"ma": "TT2", "so_cau": 3}]}},
    {"likert": {"so_muc": 6, "bien": [{"ma": "TT", "so_cau": 3}]}},
    {"thang_do": ["KHONG-CO"]},
    {"cot_chung": [{"ten": "Giới tính", "loai": "nhom"}]},
    {},
])
def test_invalid_template_config(cfg):
    with pytest.raises(LoiPhanTich):
        template.build_workbook(cfg, LIB)


# ---------- B. Tên cột kiểu Google Forms ----------

def test_google_forms_grid_headers_grouped_in_order():
    items = _pss_items()
    df = pd.DataFrame({f"Trong tháng qua, bạn có thường xuyên… [Ý {i}]": items[i] for i in range(1, 11)})
    df.insert(0, "Dấu thời gian", "2026-10-01")
    groups = group_columns(list(df.columns))
    assert groups[0]["nguon"] == "google_luoi" and len(groups[0]["cot"]) == 10
    sug = suggest_scales(df, LIB)[0]
    assert "PSS-10" in [c["ma"] for c in sug["thang_co_the"]]


def test_leading_numbered_question_text_split_into_blocks():
    cols = ["Dấu thời gian", "1. Tôi thấy khó thư giãn", "2. Tôi bị khô miệng", "3. Tôi không có cảm xúc tích cực",
            "Giới tính", "Câu 1: Tôi tin tưởng trường", "Câu 2: Tôi giới thiệu trường"]
    groups = group_columns(cols)
    assert [len(g["cot"]) for g in groups] == [3, 2]
    assert all(g["nguon"] in ("danh_so_dau_cau", "danh_so_cuoi") for g in groups)


# ---------- C. Bảng ghép câu – cột ----------

def test_mapping_table_flags_swapped_item():
    items = _pss_items(150)
    cols = [f"P{i}" for i in range(1, 11)]
    df = pd.DataFrame({f"P{i}": items[i] for i in range(1, 11)})
    ok = scales.mapping_table(df, LIB["PSS-10"], {"ma": "PSS-10", "cot": cols})
    assert not any(r["nghi_sai_vi_tri"] for r in ok)
    assert [r["cau"] for r in ok if r["dao_chieu"]] == [4, 5, 7, 8]

    # Phiếu đặt câu 3 và câu 4 đổi chỗ: cột P3 thực ra là câu 4 (đảo chiều) và ngược lại
    swapped = scales.mapping_table(df, LIB["PSS-10"], {"ma": "PSS-10", "cot": ["P1", "P2", "P4", "P3"] + cols[4:]})
    flagged = {r["cau"] for r in swapped if r["nghi_sai_vi_tri"]}
    assert flagged == {3, 4}


def test_score_report_includes_mapping_table():
    items = _pss_items(30)
    df = pd.DataFrame({f"P{i}": items[i] for i in range(1, 11)})
    _, rep = scales.score(df, LIB["PSS-10"], {"ma": "PSS-10", "cot": list(df.columns)})
    assert len(rep["bang_ghep"]) == 10 and rep["bang_ghep"][3]["dao_chieu"]
