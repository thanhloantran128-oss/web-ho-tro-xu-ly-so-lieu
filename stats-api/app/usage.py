"""Đếm lượt dùng thật: mỗi lần chạy phân tích thành công gửi một dòng sang sheet "Lượt dùng".

Chỉ gửi: phép phân tích, số dòng dữ liệu, có dùng thang đo chuẩn hay không, và mã trình duyệt ẩn danh
(chuỗi ngẫu nhiên do trình duyệt tự tạo, không gắn với ai). Không gửi dữ liệu khảo sát, tên cột hay địa chỉ IP.
Không đặt DANH_GIA_GOOGLE_URL thì không đếm.
"""
import logging
import re

from . import sheets

logger = logging.getLogger(__name__)

TEN_PHEP = {
    "thang-do": "Chấm điểm thang đo", "mo-ta": "Thống kê mô tả", "tan-suat": "Tần suất",
    "trung-binh": "Trung bình – độ lệch chuẩn", "t-test": "t-test", "anova": "ANOVA",
    "nhieu-lua-chon": "Nhiều lựa chọn", "bang-cheo": "Bảng chéo", "tuong-quan": "Tương quan",
}
_MA_HOP_LE = re.compile(r"^[a-z0-9]{16,40}$")


def ma_an_danh(value: str | None) -> str:
    """Chỉ nhận mã ngẫu nhiên đúng dạng; giá trị khác bị bỏ để không ai gửi được thông tin cá nhân vào bảng tính."""
    return value if value and _MA_HOP_LE.match(value) else ""


def record(analysis: str, so_dong: int, co_thang_do: bool, ma: str) -> None:
    """Chạy sau khi đã trả kết quả (BackgroundTasks) nên không làm chậm web; lỗi chỉ ghi log."""
    if not sheets.url():
        return
    try:
        sheets.post({"loai": "luot_dung", "phep_phan_tich": TEN_PHEP.get(analysis, analysis),
                     "so_dong": so_dong, "thang_do_chuan": "Có" if co_thang_do else "Không", "ma_trinh_duyet": ma})
    except Exception:  # noqa: BLE001 – đếm lượt không được làm hỏng phân tích
        logger.exception("Không gửi được lượt dùng sang Google Sheets")
