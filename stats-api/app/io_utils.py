"""Đọc file dữ liệu học sinh tải lên. Dữ liệu chỉ nằm trong bộ nhớ, không lưu xuống đĩa lâu dài."""
import csv
import os
import re
import tempfile
import unicodedata
from io import BytesIO, StringIO

import numpy as np
import pandas as pd

from . import data_prep, descriptives, scales
from .utils import LoiPhanTich, to_numeric

KICH_THUOC_TOI_DA = 10 * 1024 * 1024  # 10 MB
SO_NHOM_HIEN_THI = 15  # cột chữ có tối đa bấy nhiêu nhóm thì trả danh sách nhóm cho giao diện


def read_table(filename: str, content: bytes) -> tuple[pd.DataFrame, dict]:
    """Trả về (bảng dữ liệu, nhãn giá trị {cột: {giá trị: nhãn}})."""
    if len(content) > KICH_THUOC_TOI_DA:
        raise LoiPhanTich("File quá lớn (tối đa 10 MB).")
    name = (filename or "").lower()
    labels: dict = {}
    if name.endswith(".csv"):
        df = _read_csv(content)
    elif name.endswith((".xlsx", ".xls")):
        df = _read_excel(content)
    elif name.endswith(".sav"):
        df, labels = _read_sav(content)
    else:
        raise LoiPhanTich("Chỉ hỗ trợ file .csv, .xlsx, .xls hoặc .sav (SPSS).")
    df.columns = [str(c).strip() for c in df.columns]
    if df.columns.duplicated().any():
        trung = df.columns[df.columns.duplicated()].tolist()
        raise LoiPhanTich(f"Tên cột bị trùng: {trung}. Hãy đặt tên khác nhau cho mỗi cột.")
    # Ô chỉ có khoảng trắng coi như trống; chuẩn hóa chữ tiếng Việt (NFC) và bỏ khoảng trắng thừa
    df = df.replace(r"^\s*$", np.nan, regex=True)
    # Dòng trống hoàn toàn (thường ở cuối file Excel) không phải người trả lời
    df = df.dropna(how="all").reset_index(drop=True)
    for c in df.columns[df.dtypes == object]:
        df[c] = df[c].map(lambda v: unicodedata.normalize("NFC", v).strip() if isinstance(v, str) else v)
    return df, labels


SHEET_DU_LIEU = "dữ liệu"


def _read_excel(content: bytes) -> pd.DataFrame:
    """Đọc sheet tên 'Dữ liệu' nếu có (file mẫu nhập liệu), nếu không thì đọc sheet đầu tiên."""
    sheets = pd.read_excel(BytesIO(content), sheet_name=None)
    for name, df in sheets.items():
        if unicodedata.normalize("NFC", str(name)).strip().lower() in (SHEET_DU_LIEU, "du lieu"):
            return df
    return next(iter(sheets.values()))


def _read_csv(content: bytes) -> pd.DataFrame:
    """Tự nhận mã ký tự (UTF-8 hoặc Windows-1258), dấu ngăn cột (, ; tab) và dấu thập phân.
    Excel tiếng Việt thường xuất CSV dùng ';' ngăn cột và ',' thập phân."""
    for enc in ("utf-8-sig", "cp1258"):
        try:
            text = content.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise LoiPhanTich("Không đọc được bảng mã của file CSV. Hãy lưu lại dạng 'CSV UTF-8' hoặc dùng .xlsx.")
    text = unicodedata.normalize("NFC", text)
    head = "\n".join(text.splitlines()[:30])
    try:
        sep = csv.Sniffer().sniff(head, delimiters=",;\t").delimiter
    except csv.Error:
        sep = ","
    decimal = "," if sep != "," and re.search(r"\d,\d", head) else "."
    return pd.read_csv(StringIO(text), sep=sep, decimal=decimal)


def _read_sav(content: bytes):
    try:
        import pyreadstat
    except ImportError as e:  # pragma: no cover
        raise LoiPhanTich("Máy chủ chưa cài pyreadstat nên chưa đọc được file .sav.") from e
    # pyreadstat cần đường dẫn file; ghi tạm rồi xóa ngay
    fd, path = tempfile.mkstemp(suffix=".sav")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        df, meta = pyreadstat.read_sav(path)
    finally:
        os.remove(path)
    return df, dict(meta.variable_value_labels or {})


def preview(df: pd.DataFrame, library: dict, cfg: dict | None = None) -> dict:
    """Tóm tắt cấu trúc cột (không trả dữ liệu thô), gợi ý thang đo và bảng ghép câu – cột để học sinh xác nhận.
    cfg: cấu hình đọc từ sheet ẩn của file mẫu (nếu có)."""
    cols = []
    for c in df.columns:
        s = df[c]
        num = to_numeric(s)
        n_missing = int(s.isna().sum())
        is_num = num.notna().sum() == s.notna().sum() and s.notna().any()
        info = {"name": c, "n_missing": n_missing, "so_gia_tri_khac": int(s.nunique(dropna=True))}
        if is_num:
            vals = num.dropna()
            all_int = bool((vals == vals.round()).all())
            info.update(min=vals.min(), max=vals.max())
            if all_int and info["so_gia_tri_khac"] <= 11:
                info["kieu_goi_y"] = "likert_hoac_thu_bac"
            else:
                info["kieu_goi_y"] = "scale"
        else:
            info["kieu_goi_y"] = "nominal"
            if info["so_gia_tri_khac"] <= SO_NHOM_HIEN_THI:
                # Nhãn nhóm (không phải dữ liệu cá nhân) để học sinh sắp thứ tự cho biến thứ bậc
                ordered, source = descriptives.order_categories(s.dropna().astype(str).unique(), None)
                info.update(cac_gia_tri=ordered, thu_tu_tu_nhan=source == "tu_nhan")
                if source == "tu_nhan":
                    info["kieu_goi_y"] = "ordinal"
        cols.append(info)
    recode = data_prep.suggest_recode(df)
    missing = data_prep.missing_code_warnings(df)
    # Gợi ý thang đo trên dữ liệu như thể học sinh đã đồng ý đổi chữ sang số và bỏ mã thiếu
    prepared = data_prep.apply_missing_codes(df, sorted({c for w in missing for c in w["gia_tri"]}))
    prepared = data_prep.apply_recode(prepared, [{"cot": g["cot"], "bo": g["bo"]} for g in recode
                                                 if g["khop_hoan_toan"]])
    propose_types(df, cols, recode)
    out = {"n_dong": len(df), "cot": cols, "goi_y_ma_hoa_chu": recode, "canh_bao_ma_thieu": missing,
           "cau_hinh_tu_file_mau": None, "goi_y_thang_do": suggest_scales(prepared, library)}
    if cfg:
        out["cau_hinh_tu_file_mau"] = cfg
        if cfg.get("hop_le"):
            # File tạo từ mẫu: thang đo và cột đã biết chắc; kèm bảng ghép để học sinh soát lại
            for req in cfg["thang_do"]:
                req["bang_ghep"] = scales.mapping_table(prepared, library[req["ma"]], req)
            # Loại thang đo đã khai báo khi tạo mẫu được ưu tiên hơn đề xuất tự động
            for info in cols:
                declared = (cfg.get("kieu_bien") or {}).get(info["name"])
                if declared:
                    info.update(loai_de_xuat=declared["loai"], so_muc=declared.get("so_muc"), nguon_loai="file_mau")
    return out


# ---------- Đề xuất loại thang đo cho từng cột ----------
# nominal: định danh · ordinal: thứ bậc · likert: câu Likert · scale: định lượng (khoảng/tỷ lệ)
# multi: câu nhiều lựa chọn · skip: bỏ qua (dấu thời gian, câu trả lời tự do…)
LOAI_THANG_DO = ["nominal", "ordinal", "likert", "scale", "multi", "skip"]
_TEN_BO_QUA = re.compile(r"(dấu thời gian|thời gian gửi|timestamp|e-?mail|địa chỉ email|họ (và )?tên|họ tên|"
                         r"số điện thoại|^stt$|^id$|^mã (số )?(học sinh|hs)$)", re.IGNORECASE)


def propose_types(df: pd.DataFrame, cols: list[dict], recode: list[dict]):
    """Ghi 'loai_de_xuat' (và 'so_muc' với Likert) vào thông tin từng cột. Chỉ là đề xuất: học sinh xác nhận."""
    n = len(df)
    likert_text = {c: g for g in recode for c in g["cot"]}
    in_group = {c for g in group_columns(list(df.columns)) if len(g["cot"]) >= 3 for c in g["cot"]}
    for info in cols:
        col = info["name"]
        s = df[col].dropna()
        k = info["so_gia_tri_khac"]
        loai, so_muc, ly_do = "nominal", None, ""
        if _TEN_BO_QUA.search(col):
            loai, ly_do = "skip", "Tên cột là thông tin nhận dạng hoặc thời gian"
        elif s.empty:
            loai, ly_do = "skip", "Cột trống"
        elif col in likert_text:
            loai, so_muc, ly_do = "likert", len(likert_text[col]["bang"]), f"Nhãn chữ thuộc bộ “{likert_text[col]['ten']}”"
        elif info["kieu_goi_y"] == "nominal":           # cột chữ
            text = s.astype(str)
            if (text.str.contains(", ").mean() >= 0.2 and k > 3
                    and len({t.strip() for v in text for t in v.split(",")}) <= 30):
                loai, ly_do = "multi", "Nhiều ô chứa các lựa chọn nối bằng dấu phẩy"
            elif k > 30 and k > 0.5 * len(s):
                loai, ly_do = "skip", "Câu trả lời tự do (gần như mỗi người một nội dung)"
            else:
                loai, ly_do = "nominal", "Các nhóm dạng chữ"
        elif info["kieu_goi_y"] == "ordinal":
            loai, ly_do = "ordinal", "Nhãn thứ bậc quen thuộc (học lực, mức độ…)"
        else:                                          # cột số
            vals = to_numeric(s)
            all_int = bool((vals == vals.round()).all())
            lo, hi = vals.min(), vals.max()
            if k <= 2:
                loai, ly_do = "nominal", "Chỉ có 2 giá trị (nhị phân, ví dụ 0/1)"
            elif all_int and 0 <= lo and hi <= 10 and col in in_group:
                loai = "likert"
                so_muc = int(hi) if lo >= 1 else int(hi) + 1
                ly_do = "Số nguyên ít mức, thuộc nhóm câu đánh số liên tiếp"
            elif all_int and k <= 10:
                loai, ly_do = "ordinal", "Số nguyên ít mức (có thể là mã nhóm hoặc thứ bậc)"
            else:
                loai, ly_do = "scale", "Số đo có nhiều giá trị"
        info.update(loai_de_xuat=loai, so_muc=so_muc, ly_do_de_xuat=ly_do, nguon_loai="tu_dong")


# Ba kiểu tên cột có đánh số câu
_TRAILING = re.compile(r"^(.*?)[\s_.\-]*(\d+)$")                          # PSS1, DASS21_3, TT 4
_GRID = re.compile(r"^(.*\S)\s*\[(.+)\]$")                                 # Google Forms lưới: "Tiêu đề [Câu/hàng]"
_LEADING = re.compile(r"^\s*(?:câu|cau|item|q|c)?\s*(\d+)\s*[.:)\-–]\s*\S", re.IGNORECASE)  # "1. Tôi…", "Câu 2: …"


def group_columns(columns: list[str]) -> list[dict]:
    """Gom các cột có vẻ là các câu của cùng một thang, theo thứ tự câu."""
    groups, used = [], set()

    grid: dict[str, list[str]] = {}
    for c in columns:
        m = _GRID.match(c)
        if m:
            grid.setdefault(m.group(1).strip(), []).append(c)
    for title, cols in grid.items():
        if len(cols) >= 2:  # Google Forms giữ đúng thứ tự hàng của lưới
            groups.append({"tien_to": title, "cot": cols, "nguon": "google_luoi"})
            used.update(cols)

    trail: dict[str, list[tuple[int, str]]] = {}
    for c in columns:
        m = _TRAILING.match(c)
        if c not in used and m and m.group(1).strip():
            trail.setdefault(m.group(1).strip().lower(), []).append((int(m.group(2)), c))
    for prefix, items in trail.items():
        if len(items) >= 2:
            items.sort()
            groups.append({"tien_to": prefix, "cot": [c for _, c in items], "nguon": "danh_so_cuoi"})
            used.update(c for _, c in items)

    block, last = [], None
    for c in list(columns) + [None]:
        m = _LEADING.match(c) if c and c not in used else None
        n = int(m.group(1)) if m else None
        if n is None or n == 1 or last is None or n != last + 1:
            if len(block) >= 2:
                groups.append({"tien_to": f"Khối câu bắt đầu bằng “{block[0][:40]}”", "cot": block,
                               "nguon": "danh_so_dau_cau"})
            block = [c] if n is not None else []
        else:
            block.append(c)
        last = n
    return groups


def _alnum(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def suggest_scales(df: pd.DataFrame, library: dict) -> list:
    """Gợi ý thang khớp số câu và khoảng giá trị cho từng nhóm cột. Chỉ là gợi ý: học sinh phải xác nhận.
    Kèm bảng ghép câu – cột của gợi ý đầu tiên để học sinh soát thứ tự."""
    out = []
    for g in group_columns(list(df.columns)):
        cols = g["cot"]
        vals = df[cols].apply(to_numeric).stack()
        if vals.empty:
            continue
        lo, hi = vals.min(), vals.max()
        candidates = []
        for ma, spec in library.items():
            n = spec.get("so_cau")
            gv = spec.get("gia_tri") or {}
            if n != len(cols) or "min" not in gv:
                continue
            for d in (0, 1, -1):
                if lo >= gv["min"] + d and hi <= gv["max"] + d:
                    name_match = re.sub(r"[^a-z]", "", ma.lower()) in re.sub(r"[^a-z]", "", g["tien_to"].lower())
                    candidates.append({"ma": ma, "ten_viet": spec.get("ten_viet"), "lech_ma_hoa": d,
                                       "khop_ten": name_match,
                                       "khop_chinh_xac": _alnum(g["tien_to"]) == _alnum(ma) and d == 0})
                    break
        candidates.sort(key=lambda x: (not x["khop_chinh_xac"], not x["khop_ten"], x["lech_ma_hoa"] != 0))
        for cand in candidates:  # bảng ghép cho mọi gợi ý để học sinh so sánh khi chọn
            cand["bang_ghep"] = scales.mapping_table(df, library[cand["ma"]], {"ma": cand["ma"], "cot": cols})
        out.append({**g, "khoang_quan_sat": [lo, hi], "thang_co_the": candidates})
    return out
