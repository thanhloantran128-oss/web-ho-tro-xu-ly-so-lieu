"""Phiếu đánh giá ẩn danh: lưu, kiểm tra dữ liệu, tổng hợp có mã quản trị."""
import json

import pytest
from fastapi.testclient import TestClient

from app import feedback
from app.main import app

client = TestClient(app)
OK = {"huu_ich": 5, "chinh_xac": 4, "de_dung": 3, "doi_chieu": "khop_phan_lon", "gop_y": "  Cần thêm hồi quy\x07 ",
      "vai_tro": "hoc_sinh", "phep_phan_tich": "anova"}


@pytest.fixture(autouse=True)
def _tmp_file(tmp_path, monkeypatch):
    monkeypatch.setattr(feedback, "FILE", tmp_path / "danh-gia.jsonl")
    feedback._recent.clear()


def test_save_and_clean():
    r = client.post("/danh-gia", json=OK)
    assert r.status_code == 200 and r.json()["ok"]
    row = json.loads(feedback.FILE.read_text(encoding="utf-8").splitlines()[0])
    assert row["gop_y"] == "Cần thêm hồi quy" and row["huu_ich"] == 5
    assert set(row) == {"thoi_gian", *OK}  # không lưu IP hay thông tin khác


@pytest.mark.parametrize("bad", [{"huu_ich": 6}, {"chinh_xac": 0}, {"de_dung": None}, {"doi_chieu": "co"},
                                 {"gop_y": "x" * 1001}, {"vai_tro": "admin"}])
def test_invalid_rejected(bad):
    assert client.post("/danh-gia", json={**OK, **bad}).status_code == 422


def test_optional_fields_can_be_omitted():
    r = client.post("/danh-gia", json={"huu_ich": 3, "chinh_xac": 3, "de_dung": 3})
    assert r.status_code == 200


def test_rate_limit():
    for _ in range(feedback.GIOI_HAN_MOI_GIO):
        assert client.post("/danh-gia", json=OK).status_code == 200
    assert client.post("/danh-gia", json=OK).status_code == 429


def test_summary_needs_key(monkeypatch):
    client.post("/danh-gia", json=OK)
    client.post("/danh-gia", json={**OK, "huu_ich": 3, "gop_y": ""})
    monkeypatch.delenv("DANH_GIA_MA", raising=False)
    assert client.get("/danh-gia/tong-hop").status_code == 403
    monkeypatch.setenv("DANH_GIA_MA", "bi-mat")
    assert client.get("/danh-gia/tong-hop?ma=sai").status_code == 403
    s = client.get("/danh-gia/tong-hop?ma=bi-mat").json()
    assert s["so_luot"] == 2
    assert s["diem"]["huu_ich"]["trung_binh"] == 4.0 and s["diem"]["huu_ich"]["phan_bo"]["5"] == 1
    assert s["doi_chieu"]["Khớp phần lớn"] == 2 and len(s["gop_y_gan_day"]) == 1


def test_corrupt_line_is_skipped():
    feedback.FILE.parent.mkdir(parents=True, exist_ok=True)
    feedback.FILE.write_text('{"huu_ich": 4, "chinh_xac": 4, "de_dung": 4}\nkhông phải json\n', encoding="utf-8")
    assert feedback.summary()["so_luot"] == 1
