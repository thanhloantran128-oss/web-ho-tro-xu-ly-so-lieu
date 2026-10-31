"""Đề xuất loại thang đo cho từng cột và ràng buộc dùng loại đã khai báo."""
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from openpyxl import load_workbook

from app import assumptions, template
from app.io_utils import preview, read_table
from app.scales import load_library
from app.template import read_config
from app.utils import LoiPhanTich

LIB = load_library(Path(__file__).resolve().parents[2] / "scales")
RNG = np.random.default_rng(2)
N = 60


def _df():
    return pd.DataFrame({
        "Dấu thời gian": ["2026-10-01 08:00"] * N,
        "Giới tính": RNG.choice(["Nam", "Nữ"], N),
        "Khối": RNG.choice([10, 11, 12], N),
        "Học lực": RNG.choice(["Khá", "Giỏi", "Trung bình"], N),
        "CoDiLam": RNG.choice([0, 1], N),
        "GioMXH": RNG.normal(3, 1, N).round(1),
        "HT1": RNG.integers(1, 6, N), "HT2": RNG.integers(1, 6, N), "HT3": RNG.integers(1, 6, N),
        "Mức đồng ý [Câu 1]": RNG.choice(["Đồng ý", "Rất đồng ý", "Không đồng ý", "Trung lập", "Rất không đồng ý"], N),
        "Mức đồng ý [Câu 2]": RNG.choice(["Đồng ý", "Rất đồng ý", "Không đồng ý", "Trung lập", "Rất không đồng ý"], N),
        "Kênh": [", ".join(RNG.choice(["Facebook", "TikTok", "YouTube", "Zalo"], 2, replace=False)) for _ in range(N)],
        "Góp ý": [f"Ý kiến số {i}" for i in range(N)],
    })


def test_proposed_types():
    cols = {c["name"]: c for c in preview(_df(), LIB)["cot"]}
    expect = {"Dấu thời gian": "skip", "Giới tính": "nominal", "Khối": "ordinal", "Học lực": "ordinal",
              "CoDiLam": "nominal", "GioMXH": "scale", "HT1": "likert", "Mức đồng ý [Câu 1]": "likert",
              "Kênh": "multi", "Góp ý": "skip"}
    got = {k: cols[k]["loai_de_xuat"] for k in expect}
    assert got == expect
    assert cols["HT1"]["so_muc"] == 5 and cols["Mức đồng ý [Câu 1]"]["so_muc"] == 5


def test_template_stores_declared_types():
    cfg = {"cot_chung": [{"ten": "GioiTinh", "loai": "nhom", "lua_chon": ["Nam", "Nữ"]},
                         {"ten": "Gio", "loai": "so", "min": 0, "max": 24}],
           "likert": {"so_muc": 7, "bien": [{"ma": "HT", "so_cau": 2}]}, "thang_do": ["PSS-10"]}
    wb = load_workbook(BytesIO(template.build_workbook(cfg, LIB)))
    ws = wb["Dữ liệu"]
    header = [c.value for c in ws[1]]
    row = ["Nam", 2.5, 3, 4] + [1] * 10
    for c, v in enumerate(row, 1):
        ws.cell(row=2, column=c, value=v)
    buf = BytesIO()
    wb.save(buf)
    df, _ = read_table("m.xlsx", buf.getvalue())
    pv = preview(df, LIB, read_config(buf.getvalue(), list(df.columns)))
    cols = {c["name"]: c for c in pv["cot"]}
    assert cols["GioiTinh"]["loai_de_xuat"] == "nominal" and cols["Gio"]["loai_de_xuat"] == "scale"
    assert (cols["HT1"]["loai_de_xuat"], cols["HT1"]["so_muc"], cols["HT1"]["nguon_loai"]) == ("likert", 7, "file_mau")
    assert cols["PSS10_1"]["so_muc"] == 5 and header[-1] == "PSS10_10"


def test_declared_types_override_guessing():
    df = _df()
    # Khối là số nguyên 10–12: khai báo "định lượng" → không được làm biến nhóm
    with pytest.raises(LoiPhanTich, match="khai báo .Khối. là biến"):
        assumptions.check_before("anova", df, {"dv": "GioMXH", "factor": "Khối",
                                               "kieu_bien": {"Khối": {"loai": "scale"}}}, [])
    # GioMXH khai báo "định danh" → không làm biến phụ thuộc
    with pytest.raises(LoiPhanTich, match="khai báo"):
        assumptions.check_before("t-test", df, {"type": "independent", "dv": "GioMXH", "group": "Giới tính",
                                                "kieu_bien": {"GioMXH": {"loai": "nominal"}}}, [])
    # Câu Likert khai báo "likert" → cảnh báo thứ bậc dù có nhiều mức
    w = assumptions.check_before("t-test", df, {"type": "independent", "dv": "HT1", "group": "Giới tính",
                                                "kieu_bien": {"HT1": {"loai": "likert", "so_muc": 5}}}, [])
    assert w and w[0][0] == "bien_thu_bac"
    # Câu nhiều lựa chọn không dùng trong bảng chéo
    with pytest.raises(LoiPhanTich, match="nhiều lựa chọn"):
        assumptions.check_before("bang-cheo", df, {"hang": "Giới tính", "cot": "Kênh",
                                                   "kieu_bien": {"Kênh": {"loai": "multi"}}}, [])
