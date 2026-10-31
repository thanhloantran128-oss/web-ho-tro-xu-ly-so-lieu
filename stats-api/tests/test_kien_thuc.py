"""Nội dung tab Kiến thức thống kê: cấu trúc hợp lệ, liên kết từ kết quả trỏ đúng mục."""
from fastapi.testclient import TestClient

from app.main import PHAN_TICH, app

client = TestClient(app)


def test_knowledge_structure_and_links():
    k = client.get("/kien-thuc").json()
    items = [m for ch in k["chuong"] for m in ch["muc"]]
    ids = [m["id"] for m in items]
    assert len(ids) == len(set(ids)), "id mục bị trùng"
    assert all(m.get("ten") and m.get("la_gi") for m in items)
    assert all(len(r) == len(k["bang_chon_phep"]["cot"]) for r in k["bang_chon_phep"]["hang"])
    for analysis, links in k["lien_ket"].items():
        assert analysis in set(PHAN_TICH) | {"thang-do"}
        assert set(links) <= set(ids), f"liên kết hỏng ở {analysis}"
    assert set(PHAN_TICH) | {"thang-do"} <= set(k["lien_ket"]), "phép phân tích chưa có liên kết kiến thức"
