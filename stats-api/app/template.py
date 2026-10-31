"""Sinh file mẫu nhập liệu (.xlsx) theo cấu hình nghiên cứu của học sinh.

Cấu hình (JSON):
{
  "ten_de_tai": "…",                                   # tùy chọn
  "cot_chung": [                                        # câu hỏi chung (nhân khẩu học…), tùy chọn
    {"ten": "GioiTinh", "cau_hoi": "Giới tính", "loai": "nhom", "lua_chon": ["Nam", "Nữ"]},
    {"ten": "GioMXH", "loai": "so", "min": 0, "max": 24},
    {"ten": "Kenh", "loai": "nhieu_lua_chon", "lua_chon": ["Facebook", "TikTok"]}
  ],
  "likert": {"so_muc": 5, "bien": [{"ma": "TT", "ten": "Niềm tin", "so_cau": 4, "dao": [4]}]},  # tùy chọn
  "thang_do": ["PSS-10", "DASS-21"]                     # tùy chọn; để trống = bỏ qua thang đo đặc thù
}

Cấu hình được lưu vào sheet ẩn "_cau_hinh" để khi tải file lên, web tự nhận đúng thang đo, cột và câu đảo chiều.
"""
import json
import re
from io import BytesIO

from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from .utils import LoiPhanTich

FONT = "Arial"
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
EXAMPLE_FILL = PatternFill("solid", fgColor="E2EFDA")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
N_DONG_NHAP = 300
SHEET_CAU_HINH = "_cau_hinh"
PHIEN_BAN = 1
LOAI_COT = {"nhom", "so", "nhieu_lua_chon", "chu"}
TEN_HOP_LE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def scale_prefix(ma: str) -> str:
    """Tiền tố cột chuẩn cho thang đo: 'DASS-21' → 'DASS21_' (cột DASS21_1 … DASS21_21)."""
    return re.sub(r"[^A-Za-z0-9]", "", ma) + "_"


# ---------- Kiểm tra cấu hình ----------

def _plan(cfg: dict, library: dict) -> dict:
    """Chuẩn hóa cấu hình thành danh sách cột: (tên, câu hỏi, loại, giá trị hợp lệ, ghi chú, kiểm tra)."""
    cols, names = [], set()

    def add(name, question, kind, valid, note, check):
        if not TEN_HOP_LE.match(name):
            raise LoiPhanTich(f"Tên cột '{name}' không hợp lệ: chỉ dùng chữ không dấu, số và '_', bắt đầu bằng chữ.")
        if name.lower() in names:
            raise LoiPhanTich(f"Tên cột '{name}' bị trùng.")
        names.add(name.lower())
        cols.append({"ten": name, "cau_hoi": question, "loai": kind, "gia_tri": valid, "ghi_chu": note,
                     "kiem_tra": check})

    for c in cfg.get("cot_chung") or []:
        kind = c.get("loai", "chu")
        if kind not in LOAI_COT:
            raise LoiPhanTich(f"Loại cột '{kind}' không hợp lệ. Chọn một trong {sorted(LOAI_COT)}.")
        opts = [str(o) for o in c.get("lua_chon") or []]
        if kind == "nhom":
            add(c["ten"], c.get("cau_hoi", ""), "Định danh / thứ bậc", " / ".join(opts) or "Tự do",
                "Chọn từ danh sách" if opts else "Viết thống nhất", {"list": opts} if opts else None)
        elif kind == "so":
            lo, hi = c.get("min"), c.get("max")
            add(c["ten"], c.get("cau_hoi", ""), "Số đo", f"{lo} – {hi}" if lo is not None else "Số",
                "Có thể có số lẻ", {"decimal": (lo, hi)} if lo is not None and hi is not None else None)
        elif kind == "nhieu_lua_chon":
            add(c["ten"], c.get("cau_hoi", ""), "Nhiều lựa chọn", ", ".join(opts),
                "Nối các lựa chọn bằng dấu phẩy, giống Google Forms", None)
        else:
            add(c["ten"], c.get("cau_hoi", ""), "Chữ", "Tự do", "", None)

    likert = cfg.get("likert")
    if likert:
        points = likert.get("so_muc")
        if points not in (5, 7):
            raise LoiPhanTich("Thang Likert tự xây dựng chỉ nhận 5 hoặc 7 mức.")
        for b in likert.get("bien") or []:
            if not re.match(r"^[A-Za-z]([A-Za-z0-9_]*[A-Za-z_])?$", str(b.get("ma", ""))):
                raise LoiPhanTich(f"Mã biến '{b.get('ma')}' không hợp lệ: dùng chữ không dấu, không kết thúc bằng số "
                                  "(cột sẽ được đánh số TT1, TT2…).")
            n = int(b.get("so_cau", 0))
            if n < 1:
                raise LoiPhanTich(f"Biến '{b.get('ma')}' cần ít nhất 1 câu.")
            dao = set(b.get("dao") or [])
            if not dao <= set(range(1, n + 1)):
                raise LoiPhanTich(f"Câu đảo chiều của biến '{b['ma']}' phải nằm trong 1–{n}.")
            for i in range(1, n + 1):
                add(f"{b['ma']}{i}", f"{b.get('ten', b['ma'])} – câu {i}", f"Likert 1–{points}", f"1 – {points}",
                    "Câu phát biểu NGƯỢC (đảo chiều)" if i in dao else "", {"whole": (1, points)})

    for ma in cfg.get("thang_do") or []:
        spec = library.get(ma)
        if not spec or ma == "LIKERT":
            raise LoiPhanTich(f"Thang '{ma}' chưa có trong thư viện.")
        lo, hi = spec["gia_tri"]["min"], spec["gia_tri"]["max"]
        rev = set(spec.get("cau_dao_nguoc") or [])
        for i in range(1, spec["so_cau"] + 1):
            add(f"{scale_prefix(ma)}{i}", f"{spec['ten_viet']} – câu {i} (nhập nội dung từ bản tiếng Việt đã chuẩn hóa)",
                f"Thang {ma}", f"{lo} – {hi}",
                "Câu đảo chiều – vẫn ghi đúng số người trả lời chọn, hệ thống tự đảo" if i in rev else "",
                {"whole": (lo, hi)})
    if not cols:
        raise LoiPhanTich("Cấu hình chưa có cột nào.")
    return {"cols": cols, "cau_hinh": _config_for_upload(cfg, library)}


def _config_for_upload(cfg: dict, library: dict) -> dict:
    """Phần cấu hình lưu vào sheet ẩn: đúng định dạng tham số của /phan-tich."""
    out = {"phien_ban": PHIEN_BAN, "ten_de_tai": cfg.get("ten_de_tai"), "thang_do": [], "nhieu_lua_chon": [],
           "kieu_bien": {}}
    # Loại thang đo của từng cột, để khi tải lên không phải khai báo lại
    loai_chung = {"nhom": "nominal", "so": "scale", "nhieu_lua_chon": "multi", "chu": "skip"}
    for c in cfg.get("cot_chung") or []:
        out["kieu_bien"][c["ten"]] = {"loai": loai_chung.get(c.get("loai", "chu"), "nominal")}
    likert = cfg.get("likert")
    if likert:
        for b in likert.get("bien") or []:
            for i in range(1, int(b["so_cau"]) + 1):
                out["kieu_bien"][f"{b['ma']}{i}"] = {"loai": "likert", "so_muc": likert["so_muc"]}
    for ma in cfg.get("thang_do") or []:
        gv = library[ma]["gia_tri"]
        for i in range(1, library[ma]["so_cau"] + 1):
            out["kieu_bien"][f"{scale_prefix(ma)}{i}"] = {"loai": "likert", "so_muc": gv["max"] - gv["min"] + 1}
    if likert and likert.get("bien"):
        out["thang_do"].append({"ma": "LIKERT", "gia_tri": {"min": 1, "max": likert["so_muc"]},
                                "bien": [{"ma": b["ma"], "ten": b.get("ten", b["ma"]),
                                          "cot": [f"{b['ma']}{i}" for i in range(1, int(b["so_cau"]) + 1)],
                                          "dao": [f"{b['ma']}{i}" for i in b.get("dao") or []]}
                                         for b in likert["bien"]]})
    for ma in cfg.get("thang_do") or []:
        out["thang_do"].append({"ma": ma, "cot": [f"{scale_prefix(ma)}{i}"
                                                  for i in range(1, library[ma]["so_cau"] + 1)]})
    for c in cfg.get("cot_chung") or []:
        if c.get("loai") == "nhieu_lua_chon":
            out["nhieu_lua_chon"].append({"cot": c["ten"], "dang": "van_ban",
                                          "cac_lua_chon": [str(o) for o in c.get("lua_chon") or []]})
    return out


def _example(col: dict, i: int):
    chk = col["kiem_tra"] or {}
    if "list" in chk:
        return chk["list"][i % len(chk["list"])]
    if "whole" in chk:
        lo, hi = chk["whole"]
        return lo + (i * 2 + 1) % (hi - lo + 1)
    if "decimal" in chk:
        lo, hi = chk["decimal"]
        return round(lo + (hi - lo) * (0.1 + 0.05 * i), 1)
    if col["loai"] == "Nhiều lựa chọn":
        opts = [o.strip() for o in col["gia_tri"].split(",") if o.strip()]
        return ", ".join(opts[: 2 - i % 2]) if opts else None
    return None


# ---------- Sinh workbook ----------

def _header(ws, ncol):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(name=FONT, bold=True, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.freeze_panes = "A2"


def _validation(chk):
    if not chk:
        return None
    if "list" in chk:
        return DataValidation(type="list", formula1='"' + ",".join(chk["list"]) + '"', allow_blank=True,
                              errorTitle="Giá trị không hợp lệ", error="Chọn từ danh sách hoặc để trống.")
    kind = "whole" if "whole" in chk else "decimal"
    lo, hi = chk[kind]
    msg = f"Nhập số {'nguyên ' if kind == 'whole' else ''}từ {lo} đến {hi}, hoặc để trống."
    return DataValidation(type=kind, operator="between", formula1=str(lo), formula2=str(hi), allow_blank=True,
                          errorTitle="Giá trị không hợp lệ", error=msg)


GUIDE = [
    ("Ô cần điền", "Chỉ điền vào sheet 'Dữ liệu' (vùng tô vàng). KHÔNG đổi tên sheet, tên cột hay thứ tự cột: "
                   "web dựa vào đó để tự nhận thang đo và câu đảo chiều."),
    ("Ví dụ", "Xem sheet 'Ví dụ' để biết cách ghi. Không dán dòng ví dụ vào sheet 'Dữ liệu'."),
    ("1. Mỗi dòng", "Là MỘT người trả lời. Dòng 1 là tên cột; dữ liệu bắt đầu từ dòng 2."),
    ("2. Mỗi cột", "Là MỘT câu hỏi, theo đúng thứ tự trong sheet 'Từ điển biến'."),
    ("3. Thang đo", "Ghi SỐ người trả lời đã chọn, kể cả câu đảo chiều (hệ thống tự đảo). "
                    "Thang gốc bắt đầu từ 0 thì ghi đúng từ 0."),
    ("4. Ô trống", "Người không trả lời thì để TRỐNG. Không ghi NA, '-', 'không', 99 hay 999."),
    ("5. Nhóm", "Chọn từ danh sách thả xuống để viết thống nhất."),
    ("6. Nhiều lựa chọn", "Nối các lựa chọn bằng dấu phẩy trong một ô, giống Google Forms."),
    ("7. Bảo mật", "Không có họ tên, email, số điện thoại hay thông tin giúp nhận ra người trả lời."),
    ("8. Không làm", "Không gộp ô, không thêm dòng 'Tổng', không để dòng trống ở giữa bảng."),
]


def build_workbook(cfg: dict, library: dict) -> bytes:
    plan = _plan(cfg, library)
    cols = plan["cols"]
    wb = Workbook()

    ws = wb.active
    ws.title = "Dữ liệu"
    for i, col in enumerate(cols, 1):
        cell = ws.cell(row=1, column=i, value=col["ten"])
        tip = "\n".join(x for x in (col["cau_hoi"], f"Loại: {col['loai']}", f"Giá trị: {col['gia_tri']}",
                                     col["ghi_chu"]) if x)
        cell.comment = Comment(tip, "Mẫu")
        ws.column_dimensions[get_column_letter(i)].width = 28 if col["loai"] == "Nhiều lựa chọn" else 11
    _header(ws, len(cols))
    for r in range(2, N_DONG_NHAP + 2):
        for c in range(1, len(cols) + 1):
            cell = ws.cell(row=r, column=c)
            cell.fill, cell.font, cell.border = INPUT_FILL, Font(name=FONT), BORDER
    for i, col in enumerate(cols, 1):
        dv = _validation(col["kiem_tra"])
        if dv:
            letter = get_column_letter(i)
            dv.add(f"{letter}2:{letter}{N_DONG_NHAP + 1}")
            ws.add_data_validation(dv)

    ex = wb.create_sheet("Ví dụ")
    for i, col in enumerate(cols, 1):
        ex.cell(row=1, column=i, value=col["ten"])
        ex.column_dimensions[get_column_letter(i)].width = ws.column_dimensions[get_column_letter(i)].width
        for r in (2, 3):
            cell = ex.cell(row=r, column=i, value=_example(col, r - 2))
            cell.font, cell.fill, cell.border = Font(name=FONT), EXAMPLE_FILL, BORDER
    _header(ex, len(cols))
    ex.cell(row=5, column=1, value="Đây chỉ là ví dụ về cách ghi – không dán vào sheet 'Dữ liệu'.").font = Font(
        name=FONT, italic=True, color="C00000")

    cb = wb.create_sheet("Từ điển biến")
    for i, h in enumerate(["Tên cột", "Nội dung câu hỏi", "Loại biến", "Giá trị hợp lệ", "Ghi chú"], 1):
        cb.cell(row=1, column=i, value=h)
    _header(cb, 5)
    for r, col in enumerate(cols, 2):
        for c, v in enumerate((col["ten"], col["cau_hoi"], col["loai"], col["gia_tri"], col["ghi_chu"]), 1):
            cell = cb.cell(row=r, column=c, value=v)
            cell.font, cell.border = Font(name=FONT), BORDER
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for letter, w in zip("ABCDE", (14, 52, 18, 30, 44)):
        cb.column_dimensions[letter].width = w

    gd = wb.create_sheet("Hướng dẫn")
    gd.cell(row=1, column=1, value="Mục")
    gd.cell(row=1, column=2, value="Hướng dẫn")
    _header(gd, 2)
    rows = list(GUIDE)
    if cfg.get("ten_de_tai"):
        rows.insert(0, ("Đề tài", cfg["ten_de_tai"]))
    scales = [s["ma"] for s in plan["cau_hinh"]["thang_do"] if s["ma"] != "LIKERT"]
    rows.append(("Thang đo đặc thù", ", ".join(scales) if scales else "Không dùng (chỉ thang Likert tự xây dựng / câu hỏi chung)"))
    for r, (k, v) in enumerate(rows, 2):
        a, b = gd.cell(row=r, column=1, value=k), gd.cell(row=r, column=2, value=v)
        a.font, b.font = Font(name=FONT, bold=True), Font(name=FONT)
        for cell in (a, b):
            cell.alignment, cell.border = Alignment(wrap_text=True, vertical="top"), BORDER
    legend = len(rows) + 3
    gd.cell(row=legend, column=1, value="Chú thích màu").font = Font(name=FONT, bold=True)
    gd.cell(row=legend + 1, column=1).fill = INPUT_FILL
    gd.cell(row=legend + 1, column=2, value="Ô vàng: nơi điền dữ liệu (sheet 'Dữ liệu')").font = Font(name=FONT)
    gd.cell(row=legend + 2, column=1).fill = EXAMPLE_FILL
    gd.cell(row=legend + 2, column=2, value="Ô xanh: dòng ví dụ (sheet 'Ví dụ')").font = Font(name=FONT)
    gd.column_dimensions["A"].width, gd.column_dimensions["B"].width = 20, 100

    hidden = wb.create_sheet(SHEET_CAU_HINH)
    hidden["A1"] = json.dumps(plan["cau_hinh"], ensure_ascii=False)
    hidden.sheet_state = "hidden"

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def read_config(content: bytes, columns: list[str]) -> dict | None:
    """Đọc cấu hình ẩn của file mẫu. Trả None nếu không có, hoặc nếu học sinh đã đổi/xóa cột cấu hình cần."""
    try:
        wb = load_workbook(BytesIO(content), read_only=True)
    except Exception:  # noqa: BLE001 – không phải file xlsx hợp lệ thì coi như không có cấu hình
        return None
    if SHEET_CAU_HINH not in wb.sheetnames:
        return None
    raw = wb[SHEET_CAU_HINH]["A1"].value
    wb.close()
    try:
        cfg = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    needed = [c for s in cfg.get("thang_do", []) for c in (s.get("cot") or [x for b in s.get("bien", [])
                                                                             for x in b["cot"]])]
    needed += [m["cot"] for m in cfg.get("nhieu_lua_chon", [])]
    missing = [c for c in needed if c not in columns]
    if missing:
        return {"hop_le": False, "cot_bi_thieu": missing[:20],
                "thong_bao": "File được tạo từ mẫu nhưng một số cột đã bị đổi tên hoặc xóa, nên cần khai báo thang đo thủ công."}
    return {"hop_le": True, **cfg}
