"""Gửi một dòng dữ liệu tới Web App Google Apps Script (google-sheets/danh-gia.gs).

Cần hai biến môi trường: DANH_GIA_GOOGLE_URL (đường dẫn Web App) và DANH_GIA_GOOGLE_MA (mã bí mật,
trùng với MA_BI_MAT trong Apps Script). Dùng chung cho phiếu đánh giá và đếm lượt dùng.
"""
import json
import os
import urllib.request


def url() -> str | None:
    return os.environ.get("DANH_GIA_GOOGLE_URL") or None


def post(payload: dict) -> None:
    """Gửi payload (kèm mã bí mật). Lỗi mạng hoặc Apps Script từ chối thì báo lỗi để nơi gọi tự xử lý."""
    body = {"ma": os.environ.get("DANH_GIA_GOOGLE_MA", ""), **payload}
    req = urllib.request.Request(url(), data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    # Apps Script trả về chuyển hướng 302 sau khi đã ghi dòng; urllib tự đi theo chuyển hướng
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8", "replace")
    try:
        ok = json.loads(text).get("ok")
    except json.JSONDecodeError:
        ok = False
    if not ok:
        raise RuntimeError(f"Google Apps Script từ chối dữ liệu: {text[:200]}")
