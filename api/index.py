"""Điểm vào cho Vercel: chạy ứng dụng FastAPI trong stats-api/ từ thư mục gốc của kho,
để các thư mục scales/, giai-thich/, skills-hs/ được đóng gói cùng (xem vercel.json)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stats-api"))

from app.main import app  # noqa: E402,F401
