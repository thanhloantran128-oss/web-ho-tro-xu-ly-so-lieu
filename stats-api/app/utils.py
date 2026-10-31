"""Hàm dùng chung: chuyển kết quả sang JSON sạch, chuẩn hóa giá trị nhóm."""
import math

import numpy as np
import pandas as pd

SO_LE = 4  # số chữ số thập phân trả về; giao diện tự làm tròn khi hiển thị


class LoiPhanTich(ValueError):
    """Lỗi do dữ liệu hoặc tham số của người dùng; thông báo bằng tiếng Việt."""


def clean(obj):
    """Đổi kiểu numpy/pandas sang kiểu JSON, NaN/inf -> None, làm tròn số thực."""
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        f = float(obj)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, SO_LE)
    if obj is pd.NA or obj is pd.NaT:
        return None
    return obj


def to_numeric(s: pd.Series) -> pd.Series:
    """Chuyển cột sang số; ô trống hoặc chữ thành NaN."""
    return pd.to_numeric(s, errors="coerce")


def norm_value(v):
    """Chuẩn hóa giá trị để so khớp: 1, 1.0, '1' đều thành '1'."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    try:
        f = float(v)
        if f.is_integer():
            return str(int(f))
        return str(f)
    except (TypeError, ValueError):
        return str(v).strip()


def display_value(v):
    """Giá trị để trả về: số nguyên nếu được, giữ nguyên nếu là chữ."""
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return str(v)


def label_of(value, labels: dict | None):
    """Tìm nhãn của một giá trị trong bảng nhãn (nhãn từ SPSS có khóa kiểu float)."""
    if not labels:
        return str(display_value(value))
    key = norm_value(value)
    for k, lab in labels.items():
        if norm_value(k) == key:
            return lab
    return str(display_value(value))


def require_column(df: pd.DataFrame, col: str):
    if col not in df.columns:
        raise LoiPhanTich(f"Không tìm thấy cột '{col}' trong dữ liệu.")
