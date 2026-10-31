"""Đánh giá ẩn danh của người dùng về web (hữu ích, chính xác, dễ dùng) để cùng khắc phục.

- Không thu thông tin cá nhân: không tên, không email, không lưu địa chỉ IP.
- Mỗi lượt đánh giá là một dòng JSON trong file DANH_GIA_FILE (mặc định stats-api/data/danh-gia.jsonl).
"""
import json
import logging
import os
import re
import threading
import time
import urllib.request
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)
FILE = Path(os.environ.get("DANH_GIA_FILE", Path(__file__).resolve().parents[1] / "data" / "danh-gia.jsonl"))
_lock = threading.Lock()

CAU_HOI = {
    "huu_ich": "Web giúp ích cho việc xử lý số liệu của bạn ở mức nào?",
    "chinh_xac": "Bạn thấy kết quả và lời giải thích của web chính xác, đáng tin cậy ở mức nào?",
    "doi_chieu": "Nếu đã đối chiếu với SPSS, Excel hoặc phần mềm khác, kết quả có khớp không?",
    "de_dung": "Các bước thao tác trên web dễ hiểu, dễ làm ở mức nào?",
    "gop_y": "Điều gì cần khắc phục hoặc bổ sung?",
}
DOI_CHIEU = ["khop_hoan_toan", "khop_phan_lon", "khong_khop", "chua_doi_chieu"]
TEN_DOI_CHIEU = {"khop_hoan_toan": "Khớp hoàn toàn", "khop_phan_lon": "Khớp phần lớn",
                 "khong_khop": "Không khớp", "chua_doi_chieu": "Chưa đối chiếu"}
TEN_VAI_TRO = {"hoc_sinh": "Học sinh", "giao_vien": "Giáo viên", "khac": "Khác"}
DO_DAI_GOP_Y = 1000


class DanhGia(BaseModel):
    huu_ich: int = Field(ge=1, le=5)
    chinh_xac: int = Field(ge=1, le=5)
    doi_chieu: Literal["khop_hoan_toan", "khop_phan_lon", "khong_khop", "chua_doi_chieu"] | None = None
    de_dung: int = Field(ge=1, le=5)
    gop_y: str = Field(default="", max_length=DO_DAI_GOP_Y)
    vai_tro: Literal["hoc_sinh", "giao_vien", "khac"] | None = None
    phep_phan_tich: str | None = Field(default=None, max_length=40)

    @field_validator("gop_y")
    @classmethod
    def _clean(cls, v: str) -> str:
        # Bỏ ký tự điều khiển; góp ý chỉ được hiển thị dạng văn bản thuần
        return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", v).strip()


# Giới hạn gửi để tránh spam (chỉ giữ trong bộ nhớ, không lưu IP xuống đĩa)
GIOI_HAN_MOI_GIO = 10
_recent: dict[str, deque] = defaultdict(deque)


def allow(client_key: str) -> bool:
    now = time.time()
    q = _recent[client_key]
    while q and now - q[0] > 3600:
        q.popleft()
    if len(q) >= GIOI_HAN_MOI_GIO:
        return False
    q.append(now)
    return True


def save(item: DanhGia) -> str:
    """Lưu một phiếu. Có DANH_GIA_GOOGLE_URL thì gửi sang Google Sheets (lưu lâu dài, dùng khi chạy trên Render);
    nếu không, hoặc gửi lỗi, thì ghi vào file. Trả về nơi đã lưu: "google_sheets" hoặc "file"."""
    row = {"thoi_gian": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), **item.model_dump()}
    url = os.environ.get("DANH_GIA_GOOGLE_URL")
    if url:
        try:
            _send_to_sheets(url, row)
            return "google_sheets"
        except Exception:  # noqa: BLE001 – không để mất phiếu chỉ vì Google lỗi tạm thời
            logger.exception("Không gửi được phiếu đánh giá sang Google Sheets; ghi tạm vào file")
    with _lock:
        FILE.parent.mkdir(parents=True, exist_ok=True)
        with FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return "file"


def _send_to_sheets(url: str, row: dict) -> None:
    """Gửi phiếu tới Web App Google Apps Script (google-sheets/danh-gia.gs) – nhãn tiếng Việt cho dễ đọc trên bảng tính."""
    payload = {
        "ma": os.environ.get("DANH_GIA_GOOGLE_MA", ""),
        "thoi_gian": row["thoi_gian"],
        "vai_tro": TEN_VAI_TRO.get(row.get("vai_tro"), ""),
        "phep_phan_tich": row.get("phep_phan_tich") or "",
        "huu_ich": row["huu_ich"], "chinh_xac": row["chinh_xac"], "de_dung": row["de_dung"],
        "doi_chieu": TEN_DOI_CHIEU.get(row.get("doi_chieu"), ""),
        "gop_y": row.get("gop_y", ""),
    }
    req = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    # Apps Script trả về chuyển hướng 302 sau khi đã ghi dòng; urllib tự đi theo chuyển hướng
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8", "replace")
    try:
        ok = json.loads(body).get("ok")
    except json.JSONDecodeError:
        ok = False
    if not ok:
        raise RuntimeError(f"Google Apps Script từ chối phiếu: {body[:200]}")


def load() -> list[dict]:
    if not FILE.exists():
        return []
    rows = []
    for line in FILE.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # bỏ qua dòng hỏng, không làm hỏng cả tổng hợp
    return rows


def summary(rows: list[dict] | None = None, so_gop_y: int = 50) -> dict:
    rows = load() if rows is None else rows
    out = {"so_luot": len(rows), "cau_hoi": CAU_HOI, "diem": {}, "doi_chieu": {}, "vai_tro": {}, "phep_phan_tich": {},
           "gop_y_gan_day": []}
    for key in ("huu_ich", "chinh_xac", "de_dung"):
        vals = [r[key] for r in rows if isinstance(r.get(key), int)]
        dist = Counter(vals)
        out["diem"][key] = {"trung_binh": round(sum(vals) / len(vals), 2) if vals else None, "n": len(vals),
                            "phan_bo": {str(k): dist.get(k, 0) for k in range(1, 6)},
                            "ty_le_4_5": round(sum(1 for v in vals if v >= 4) / len(vals) * 100, 1) if vals else None}
    out["doi_chieu"] = {TEN_DOI_CHIEU[k]: sum(1 for r in rows if r.get("doi_chieu") == k) for k in DOI_CHIEU}
    out["vai_tro"] = dict(Counter(TEN_VAI_TRO.get(r.get("vai_tro"), "Không nêu") for r in rows))
    out["phep_phan_tich"] = dict(Counter(r.get("phep_phan_tich") or "không rõ" for r in rows).most_common())
    out["gop_y_gan_day"] = [{"thoi_gian": r.get("thoi_gian"), "huu_ich": r.get("huu_ich"), "chinh_xac": r.get("chinh_xac"),
                             "de_dung": r.get("de_dung"), "doi_chieu": TEN_DOI_CHIEU.get(r.get("doi_chieu"), ""),
                             "phep_phan_tich": r.get("phep_phan_tich"), "gop_y": r["gop_y"]}
                            for r in reversed(rows) if r.get("gop_y")][:so_gop_y]
    return out
