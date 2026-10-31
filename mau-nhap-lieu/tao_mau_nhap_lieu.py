"""Tạo file mẫu nhập liệu chung: mau-nhap-lieu.xlsx (không dùng thang đo đặc thù).
Trên web, học sinh tự tạo file mẫu riêng cho đề tài qua POST /mau-nhap-lieu.
Chạy (trong thư mục stats-api): .venv\\Scripts\\python ..\\mau-nhap-lieu\\tao_mau_nhap_lieu.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stats-api"))

from app.scales import load_library  # noqa: E402
from app.template import build_workbook  # noqa: E402

CAU_HINH = {
    "ten_de_tai": "Mẫu chung – đổi theo đề tài của bạn",
    "cot_chung": [
        {"ten": "GioiTinh", "cau_hoi": "Giới tính của bạn", "loai": "nhom", "lua_chon": ["Nam", "Nữ"]},
        {"ten": "Khoi", "cau_hoi": "Bạn đang học khối nào?", "loai": "nhom", "lua_chon": ["10", "11", "12"]},
        {"ten": "GioMXH", "cau_hoi": "Trung bình mỗi ngày bạn dùng mạng xã hội bao nhiêu giờ?", "loai": "so",
         "min": 0, "max": 24},
        {"ten": "KenhThongTin", "cau_hoi": "Bạn tìm thông tin học tập qua những kênh nào? (chọn nhiều)",
         "loai": "nhieu_lua_chon",
         "lua_chon": ["Facebook", "TikTok", "Website, báo điện tử", "Bạn bè, người thân", "YouTube"]},
    ],
    "likert": {"so_muc": 5, "bien": [{"ma": "TT", "ten": "Hứng thú học tập", "so_cau": 4, "dao": [4]}]},
    "thang_do": [],
}

if __name__ == "__main__":
    out = Path(__file__).with_name("mau-nhap-lieu.xlsx")
    out.write_bytes(build_workbook(CAU_HINH, load_library(ROOT / "scales")))
    print(f"Đã tạo {out}")
