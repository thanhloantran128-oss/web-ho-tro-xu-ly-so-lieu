"""API máy tính thống kê.

Chạy:  uvicorn app.main:app --reload   (trong thư mục stats-api)
Dữ liệu tải lên chỉ được xử lý trong bộ nhớ cho từng yêu cầu và không được lưu lại.
"""
import json
import logging
import os
import re
import secrets
from pathlib import Path

import anthropic
import yaml
from fastapi import BackgroundTasks, FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import (ai, anova, assumptions, correlation, crosstab, data_prep, descriptives, explain_rules, feedback,
               multiresponse, template, ttest, usage)
from .io_utils import preview, read_table
from .scales import apply_all, load_library, rename_warnings
from .utils import LoiPhanTich, clean

logger = logging.getLogger(__name__)
SCALES_DIR = Path(__file__).resolve().parents[2] / "scales"
LIBRARY = load_library(SCALES_DIR)

# Vercel (serverless) có thể dừng hàm ngay sau khi trả kết quả, nên tác vụ nền phải chạy trước khi trả
SERVERLESS = bool(os.environ.get("VERCEL"))

app = FastAPI(title="Máy tính thống kê cho học sinh", version="0.1.0")

PHAN_TICH = {
    "mo-ta": lambda df, p, lab: descriptives.describe(df, p, lab),
    "tan-suat": lambda df, p, lab: descriptives.frequencies(df, p, lab),
    "trung-binh": lambda df, p, lab: descriptives.means(df, p),
    "t-test": ttest.run,
    "anova": anova.run,
    "nhieu-lua-chon": multiresponse.run,
    "bang-cheo": crosstab.run,
    "tuong-quan": correlation.run,
}


@app.get("/thang-do")
def list_scales():
    """Menu thang đo đặc thù trong thư viện (không kèm nội dung câu hỏi). Thang Likert tự xây dựng không nằm
    trong menu này mà được khai báo riêng."""
    out = []
    for s in LIBRARY.values():
        if s["ma"] == "LIKERT":
            continue
        subs = [t["ma"] for t in s.get("tieu_thang") or []]
        has_total = (s.get("diem_tong") or {}).get("cach_tinh", "khong_co") != "khong_co"
        out.append({"ma": s["ma"], "ten_viet": s.get("ten_viet"), "so_cau": s.get("so_cau"),
                    "gia_tri": s.get("gia_tri"), "cau_dao_nguoc": s.get("cau_dao_nguoc") or [],
                    "nhay_cam": s.get("nhay_cam", False),
                    # Tên cột điểm được thêm vào dữ liệu sau khi chấm, dùng làm biến cho t-test/ANOVA
                    "cot_diem": [{"cot": f"{s['ma']}_{c}", "ten": t.get("ten", c)}
                                 for c, t in zip(subs, s.get("tieu_thang") or [])]
                                + ([{"cot": f"{s['ma']}_TONG", "ten": "Điểm tổng"}] if has_total else [])})
    return out


KIEN_THUC = yaml.safe_load((Path(__file__).resolve().parents[2] / "giai-thich" / "kien-thuc.yaml")
                           .read_text(encoding="utf-8"))


@app.get("/kien-thuc")
def kien_thuc():
    """Nội dung tab Kiến thức thống kê (giai-thich/kien-thuc.yaml)."""
    return KIEN_THUC


@app.post("/danh-gia")
def danh_gia(item: feedback.DanhGia, request: Request):
    """Nhận đánh giá ẩn danh của người dùng."""
    client = request.client.host if request.client else "?"
    if not feedback.allow(client):
        raise HTTPException(status_code=429, detail="Bạn đã gửi nhiều đánh giá trong thời gian ngắn. Cảm ơn bạn, hãy thử lại sau.")
    feedback.save(item)
    return {"ok": True, "thong_bao": "Cảm ơn bạn đã đánh giá!"}


@app.get("/danh-gia/tong-hop")
def danh_gia_tong_hop(ma: str = ""):
    """Tổng hợp đánh giá – chỉ mở khi máy chủ đặt biến môi trường DANH_GIA_MA và yêu cầu gửi đúng mã ?ma=…"""
    key = os.environ.get("DANH_GIA_MA")
    if not key or not secrets.compare_digest(ma, key):
        raise HTTPException(status_code=403, detail="Cần mã quản trị để xem tổng hợp đánh giá.")
    return feedback.summary()


@app.get("/rang-buoc")
def rang_buoc():
    """Lời giải thích ràng buộc t-test/ANOVA (giai-thich/rang-buoc.yaml) để giao diện cảnh báo ngay khi chọn biến."""
    return assumptions.R


@app.get("/cau-hinh")
def cau_hinh():
    """Giao diện dùng để biết có bật phần hỏi đáp AI hay không."""
    # Vercel giới hạn yêu cầu gửi lên khoảng 4,5 MB
    return {"co_ai": bool(os.environ.get("ANTHROPIC_API_KEY")), "kich_thuoc_toi_da_mb": 4 if SERVERLESS else 10,
            "goatcounter": _goatcounter_code()}


def _goatcounter_code() -> str | None:
    """Mã GoatCounter (đếm lượt truy cập, không dùng cookie) – đặt bằng biến môi trường GOATCOUNTER_CODE."""
    code = os.environ.get("GOATCOUNTER_CODE", "").strip().lower()
    # Chấp nhận cả khi dán nguyên địa chỉ: https://ten.goatcounter.com/ → ten
    code = re.sub(r"^https?://", "", code).split("/")[0].removesuffix(".goatcounter.com")
    return code if re.fullmatch(r"[a-z0-9-]{2,50}", code) else None


@app.post("/mau-nhap-lieu")
def mau_nhap_lieu(cfg: dict):
    """Sinh file Excel mẫu theo cấu hình nghiên cứu (xem app/template.py).
    'thang_do' để trống = bỏ qua thang đo đặc thù, chỉ cần câu hỏi chung và/hoặc Likert tự xây dựng."""
    try:
        content = template.build_workbook(cfg, LIBRARY)
    except LoiPhanTich as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(content=content,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="mau-nhap-lieu.xlsx"'})


@app.post("/xem-truoc")
async def xem_truoc(file: UploadFile = File(...)):
    """Cấu trúc cột, gợi ý thang đo và bảng ghép câu – cột – không trả dữ liệu thô.
    File tạo từ /mau-nhap-lieu được nhận cấu hình tự động (trường 'cau_hinh_tu_file_mau')."""
    try:
        content = await file.read()
        df, labels = read_table(file.filename, content)
        cfg = template.read_config(content, list(df.columns)) if file.filename.lower().endswith(".xlsx") else None
        return clean(preview(df, LIBRARY, cfg, labels))
    except LoiPhanTich as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/phan-tich")
async def phan_tich(background: BackgroundTasks, file: UploadFile = File(...), params: str = Form(...),
                    x_ma_an_danh: str | None = Header(default=None)):
    """params (JSON):
    {
      "analysis": "thang-do" | "mo-ta" | "tan-suat" | "trung-binh" | "t-test" | "anova" | "nhieu-lua-chon",
      "ma_thieu": [99, 999],                                   # mã 'không trả lời' học sinh đã xác nhận
      "nhan_gia_tri": {"GioiTinh": {"1": "Nam", "2": "Nữ"}},   # nhãn giá trị học sinh tự điền (không bắt buộc)
      "ma_hoa_chu": [{"cot": ["TT1", "TT2"], "bo": "dong_y_5"}],  # đổi chữ Likert sang số (đã xác nhận)
      "thang_do": [{"ma": "DASS-21", "cot": ["Q1", ..., "Q21"], "dich_chuyen": null}],
      ... tham số riêng của từng phép phân tích (xem docstring trong từng module)
    }
    Các cột điểm thang đo (ví dụ "DASS-21_D", "TT") được thêm vào dữ liệu trước khi phân tích,
    nên có thể dùng làm biến phụ thuộc cho t-test/ANOVA."""
    try:
        p = json.loads(params)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Tham số không phải JSON hợp lệ.")
    try:
        df, labels = read_table(file.filename, await file.read())
        labels = data_prep.merge_value_labels(labels, p.get("nhan_gia_tri"), df)
        df = data_prep.prepare(df, p)
        warnings = data_prep.data_warnings(df)
        df, scale_reports = apply_all(df, LIBRARY, p.get("thang_do"))
        warnings += rename_warnings(scale_reports)
        analysis = p.get("analysis")
        not_ready = [r for r in scale_reports if r["trang_thai"] != "ok"]
        if analysis == "thang-do" or not_ready:
            # Chưa chấm điểm được thì không chạy tiếp để tránh phân tích trên điểm sai
            if not not_ready:
                _sau_khi_tra(background, usage.record, "thang-do", len(df), True, usage.ma_an_danh(x_ma_an_danh))
            return _with_explanation({"analysis": "thang-do", "ket_qua_thang_do": scale_reports,
                                      "ghi_chu_do_tin_cay": explain_rules.L["thang-do"]["ghi_chu_tieu_chi"]}, warnings)
        if analysis not in PHAN_TICH:
            raise LoiPhanTich(f"Phép phân tích '{analysis}' chưa được hỗ trợ.")
        # Ràng buộc theo loại thang đo: lỗi nghiêm trọng dừng tại đây (LoiPhanTich), cảnh báo đi kèm kết quả
        pending = assumptions.check_before(analysis, df, p, scale_reports)
        result = PHAN_TICH[analysis](df, p, labels)
        if scale_reports:
            result["thang_do"] = [r["scale"] for r in scale_reports]
        result["kiem_tra_dieu_kien"] = assumptions.finish(pending, result)
        _sau_khi_tra(background, usage.record, analysis, len(df), bool(scale_reports), usage.ma_an_danh(x_ma_an_danh))
        return _with_explanation(result, result["kiem_tra_dieu_kien"] + warnings)
    except LoiPhanTich as e:
        raise HTTPException(status_code=400, detail=str(e))


def _sau_khi_tra(background: BackgroundTasks, fn, *args) -> None:
    """Chạy fn sau khi trả kết quả (không làm chậm web); trên Vercel chạy ngay vì hàm có thể bị dừng sau khi trả."""
    if SERVERLESS:
        fn(*args)
    else:
        background.add_task(fn, *args)


def _with_explanation(result: dict, warnings: list[str]) -> dict:
    """Gắn lời giải thích tự động (không dùng AI). Lỗi giải thích không được làm hỏng kết quả tính."""
    result["canh_bao_du_lieu"] = warnings
    try:
        result["giai_thich"] = explain_rules.giai_thich(result)
        result["giai_thich"]["canh_bao"] = warnings + result["giai_thich"]["canh_bao"]
    except Exception:  # noqa: BLE001
        logger.exception("Không tạo được giải thích tự động")
        result["giai_thich"] = None
    return clean(result)


class YeuCauGiaiThich(BaseModel):
    ket_qua: dict              # JSON trả về từ /phan-tich
    cau_hoi: str
    lich_su: list[dict] = []   # [{"role": "user"|"assistant", "content": "..."}] các lượt trước


@app.post("/giai-thich")
def giai_thich(req: YeuCauGiaiThich):
    """AI giải thích bảng kết quả theo bộ skill. Chỉ nhận kết quả đã tính, không nhận dữ liệu thô."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail="Máy chủ chưa cấu hình ANTHROPIC_API_KEY.")
    try:
        return ai.explain(req.ket_qua, req.cau_hoi, req.lich_su)
    except LoiPhanTich as e:
        raise HTTPException(status_code=400, detail=str(e))
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="Trợ lý đang quá tải, bạn thử lại sau ít phút nhé.")
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=503, detail="Khóa API của máy chủ không hợp lệ.")
    except anthropic.APIConnectionError:
        raise HTTPException(status_code=503, detail="Không kết nối được tới dịch vụ AI.")
    except anthropic.APIStatusError as e:
        raise HTTPException(status_code=502, detail=f"Dịch vụ AI báo lỗi ({e.status_code}).")


# Giao diện web (HTML/JS tĩnh) – gắn sau cùng để không che các đường dẫn API ở trên
WEB_DIR = Path(__file__).resolve().parents[1] / "web"
if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
