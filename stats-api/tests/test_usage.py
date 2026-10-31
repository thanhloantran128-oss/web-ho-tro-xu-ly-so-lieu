"""Đếm lượt dùng: chỉ gửi thông tin tổng quát, không gửi dữ liệu khảo sát; lỗi gửi không làm hỏng phân tích."""
import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import sheets, usage
from app.main import app

client = TestClient(app)
MA = "a1b2c3d4e5f6a7b8c9d0"
DF = pd.DataFrame({"Diem": [3, 4, 5, 2, 4, 5, 3, 4], "GioiTinh": ["Nam", "Nữ"] * 4})


def _run(params, headers=None):
    files = {"file": ("data.csv", DF.to_csv(index=False).encode("utf-8-sig"), "text/csv")}
    return client.post("/phan-tich", files=files, data={"params": json.dumps(params)}, headers=headers or {})


@pytest.fixture
def sent(monkeypatch):
    rows = []
    monkeypatch.setenv("DANH_GIA_GOOGLE_URL", "https://script.google.com/macros/s/abc/exec")
    monkeypatch.setenv("DANH_GIA_GOOGLE_MA", "bi-mat")
    monkeypatch.setattr(sheets, "post", lambda payload: rows.append(payload))
    return rows


def test_successful_analysis_is_counted(sent):
    r = _run({"analysis": "mo-ta", "variables": [{"name": "Diem", "type": "scale"}]}, {"X-Ma-An-Danh": MA})
    assert r.status_code == 200, r.text
    assert sent == [{"loai": "luot_dung", "phep_phan_tich": "Thống kê mô tả", "so_dong": 8,
                     "thang_do_chuan": "Không", "ma_trinh_duyet": MA}]
    assert "Diem" not in json.dumps(sent, ensure_ascii=False)   # không gửi tên cột hay dữ liệu


def test_failed_analysis_not_counted(sent):
    assert _run({"analysis": "anova", "dv": "GioiTinh", "factor": "Diem"}).status_code == 400
    assert sent == []


@pytest.mark.parametrize("bad", ["", "ngan", "Nguyen Van A <a@b.com>", "x" * 41])
def test_only_random_ids_accepted(bad):
    assert usage.ma_an_danh(bad) == ""
    assert usage.ma_an_danh(MA) == MA


def test_sheets_error_does_not_break_analysis(monkeypatch):
    monkeypatch.setenv("DANH_GIA_GOOGLE_URL", "https://script.google.com/macros/s/abc/exec")

    def boom(payload):
        raise RuntimeError("mạng lỗi")

    monkeypatch.setattr(sheets, "post", boom)
    assert _run({"analysis": "mo-ta", "variables": [{"name": "Diem", "type": "scale"}]}).status_code == 200


def test_no_url_no_count(monkeypatch):
    monkeypatch.delenv("DANH_GIA_GOOGLE_URL", raising=False)
    monkeypatch.setattr(sheets, "post", lambda payload: pytest.fail("không được gửi"))
    assert _run({"analysis": "mo-ta", "variables": [{"name": "Diem", "type": "scale"}]}).status_code == 200


@pytest.mark.parametrize("value,expected", [("xu-ly-so-lieu", "xu-ly-so-lieu"), ("", None),
                                            ("a.evil.com/x", None), (" Ten-Web ", "ten-web")])
def test_goatcounter_code(monkeypatch, value, expected):
    monkeypatch.setenv("GOATCOUNTER_CODE", value)
    assert client.get("/cau-hinh").json()["goatcounter"] == expected
