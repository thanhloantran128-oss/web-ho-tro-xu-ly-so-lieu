"""Chuẩn bị dữ liệu trước khi phân tích:
- Đổi nhãn chữ của câu Likert (Google Forms "Lưới trắc nghiệm" xuất ra chữ) sang số – chỉ khi học sinh xác nhận.
- Phát hiện mã thiếu kiểu SPSS (99, 999…) và chuyển thành ô trống – chỉ khi học sinh xác nhận.
"""
import unicodedata

import pandas as pd

from .utils import LoiPhanTich, require_column, to_numeric

# Bộ nhãn chữ thường gặp trong phiếu khảo sát tiếng Việt → điểm (thang 5 mức, bắt đầu từ 1).
# Thang gốc bắt đầu từ 0 (PSS-10, DASS-21…) sẽ được bước chấm điểm thang đo phát hiện lệch 1 và hỏi xác nhận.
BO_NHAN = {
    "dong_y_5": {
        "ten": "Mức độ đồng ý (5 mức)",
        "nhan": {1: ["rất không đồng ý", "hoàn toàn không đồng ý"],
                 2: ["không đồng ý"],
                 3: ["trung lập", "bình thường", "phân vân", "không ý kiến", "không có ý kiến",
                     "không đồng ý cũng không phản đối", "trung hòa"],
                 4: ["đồng ý"],
                 5: ["rất đồng ý", "hoàn toàn đồng ý"]}},
    "tan_suat_5": {
        "ten": "Tần suất (5 mức)",
        "nhan": {1: ["không bao giờ"], 2: ["hiếm khi", "hầu như không"], 3: ["thỉnh thoảng", "đôi khi"],
                 4: ["thường xuyên", "khá thường xuyên"], 5: ["rất thường xuyên", "luôn luôn"]}},
    "hai_long_5": {
        "ten": "Mức độ hài lòng (5 mức)",
        "nhan": {1: ["rất không hài lòng"], 2: ["không hài lòng"], 3: ["bình thường", "trung lập"],
                 4: ["hài lòng"], 5: ["rất hài lòng"]}},
    "muc_do_5": {
        "ten": "Mức độ (5 mức)",
        "nhan": {1: ["rất thấp", "rất ít"], 2: ["thấp", "ít"], 3: ["trung bình", "vừa phải"],
                 4: ["cao", "nhiều"], 5: ["rất cao", "rất nhiều"]}},
}

MA_THIEU_PHO_BIEN = {99, 999, 9999, -99, -999}

# Các thang thứ bậc chữ thường gặp, xếp từ thấp đến cao (dùng để sắp bảng tần số và % tích lũy)
THU_TU_BIET = [
    ["kém", "yếu", "trung bình", "khá", "giỏi", "xuất sắc"],
    ["chưa đạt", "đạt", "khá", "tốt"],
    ["rất thấp", "thấp", "trung bình", "cao", "rất cao"],
    ["rất ít", "ít", "vừa phải", "nhiều", "rất nhiều"],
    ["chưa bao giờ", "1 lần", "2 lần", "3 lần", "nhiều lần"],
] + [[lab for d in sorted(b["nhan"]) for lab in b["nhan"][d]] for b in BO_NHAN.values()]


def known_order(values) -> list | None:
    """Nếu mọi giá trị chữ đều thuộc một thang thứ bậc đã biết, trả về các giá trị đó theo thứ tự thấp → cao."""
    vals = [v for v in values if isinstance(v, str)]
    if len(vals) < 2 or len(vals) != len(list(values)):
        return None
    norm = {v: _norm(v) for v in vals}
    for scale in THU_TU_BIET:
        rank = {lab: i for i, lab in enumerate(scale)}
        if all(n in rank for n in norm.values()):
            return sorted(vals, key=lambda v: rank[norm[v]])
    return None
SO_O_LOI_TOI_DA = 20


def _norm(s) -> str:
    return " ".join(unicodedata.normalize("NFC", str(s)).lower().split())


def _bang_phang(bo: str) -> dict[str, int]:
    return {_norm(lab): diem for diem, labs in BO_NHAN[bo]["nhan"].items() for lab in labs}


# ---------- Đổi chữ sang số ----------

def suggest_recode(df: pd.DataFrame) -> list[dict]:
    """Gợi ý cột chữ có thể đổi sang số. 'khop_hoan_toan' = mọi giá trị đều nằm trong bộ nhãn."""
    groups: dict[str, dict] = {}
    for col in df.columns:
        s = df[col].dropna()
        if s.empty or to_numeric(s).notna().all():
            continue
        values = {_norm(v) for v in s.astype(str)}
        if len(values) < 2 or len(values) > 7:
            continue
        best = None
        for bo in BO_NHAN:
            table = _bang_phang(bo)
            matched = values & table.keys()
            if len(matched) >= max(2, len(values) // 2 + 1) and (best is None or len(matched) > best[1]):
                best = (bo, len(matched), sorted(values - table.keys()))
        if best:
            bo, _, unmatched = best
            key = bo if not unmatched else f"{bo}:{col}"
            g = groups.setdefault(key, {"bo": bo, "ten": BO_NHAN[bo]["ten"], "cot": [],
                                        "khop_hoan_toan": not unmatched, "gia_tri_chua_khop": unmatched,
                                        "bang": {labs[0]: d for d, labs in BO_NHAN[bo]["nhan"].items()}})
            g["cot"].append(col)
    return list(groups.values())


def apply_recode(df: pd.DataFrame, specs: list | None) -> pd.DataFrame:
    """specs: [{"cot": [...], "bo": "dong_y_5"} hoặc {"cot": [...], "bang": {"Đồng ý": 4, ...}}]"""
    if not specs:
        return df
    df = df.copy()
    for spec in specs:
        if spec.get("bang"):
            table = {_norm(k): v for k, v in spec["bang"].items()}
        elif spec.get("bo") in BO_NHAN:
            table = _bang_phang(spec["bo"])
        else:
            raise LoiPhanTich("Mỗi mục đổi chữ sang số cần 'bo' (bộ nhãn có sẵn) hoặc 'bang' (bảng tự khai báo).")
        for col in spec.get("cot") or []:
            require_column(df, col)
            s = df[col]
            mapped = s.map(lambda v: v if pd.isna(v) else table.get(_norm(v), to_numeric(pd.Series([v])).iloc[0]))
            bad = s.notna() & mapped.isna()
            if bad.any():
                raise LoiPhanTich(f"Cột '{col}' có giá trị chưa có trong bảng đổi: "
                                  f"{sorted({str(v) for v in s[bad]})}. Hãy bổ sung vào bảng.")
            df[col] = mapped.astype(float)
    return df


# ---------- Mã thiếu ----------

def missing_code_warnings(df: pd.DataFrame) -> list[dict]:
    """Cột số có 99/999… trong khi các giá trị khác đều nhỏ: nhiều khả năng là mã 'không trả lời' kiểu SPSS."""
    out = []
    for col in df.columns:
        s = df[col].dropna()
        num = to_numeric(s)
        if s.empty or num.isna().any():
            continue
        codes = sorted(set(num) & MA_THIEU_PHO_BIEN)
        if not codes:
            continue
        others = num[~num.isin(codes)]
        if others.empty or others.abs().max() < min(abs(c) for c in codes) / 2:
            rows = [int(i) + 2 for i in num.index[num.isin(codes)][:SO_O_LOI_TOI_DA]]
            out.append({"cot": col, "gia_tri": codes, "so_o": int(num.isin(codes).sum()), "dong": rows})
    return out


def apply_missing_codes(df: pd.DataFrame, codes: list | None) -> pd.DataFrame:
    """Chuyển các mã thiếu học sinh đã xác nhận thành ô trống (chỉ ở cột số)."""
    if not codes:
        return df
    df = df.copy()
    codes = [float(c) for c in codes]
    for col in df.columns:
        num = to_numeric(df[col])
        if num.notna().sum() == df[col].notna().sum():
            df.loc[num.isin(codes), col] = pd.NA
    return df


def prepare(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    df = apply_missing_codes(df, p.get("ma_thieu"))
    return apply_recode(df, p.get("ma_hoa_chu"))


def data_warnings(df: pd.DataFrame) -> list[str]:
    """Cảnh báo về dữ liệu còn tồn tại sau bước chuẩn bị (hiện kèm mọi kết quả phân tích)."""
    out = []
    for w in missing_code_warnings(df):
        out.append(f"Cột **{w['cot']}** có {w['so_o']} ô mang giá trị {', '.join(map(str, w['gia_tri']))} "
                   "trong khi các giá trị khác đều nhỏ. Đây có thể là mã 'không trả lời' kiểu SPSS và sẽ bị tính "
                   "như số thật, làm sai trung bình. Nếu đúng, hãy xác nhận chuyển thành ô trống.")
    for g in suggest_recode(df):
        cols = g["cot"]
        names = ", ".join(cols) if len(cols) <= 3 else f"{cols[0]} … {cols[-1]}"
        out.append(f"{len(cols)} cột ({names}) đang là chữ ({g['ten']}). Hãy đổi sang số ở bước 1 trước khi tính "
                   "trung bình hoặc chấm điểm thang đo.")
    return out
