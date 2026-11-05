"""Kiểm tra chất lượng phiếu trả lời trước khi phân tích (phỏng theo scholar-eda, rút gọn cho THPT).

Chỉ trả về SỐ DÒNG của phiếu nghi vấn (đánh số như Excel: dòng 2 là người trả lời đầu tiên), không trả dữ liệu.
Web không tự loại phiếu nào: học sinh xem lý do rồi tự quyết định; số dòng đã chọn được gửi lại trong
tham số 'loai_dong' của /phan-tich.
"""
from pathlib import Path

import pandas as pd
import yaml

from .data_prep import _bang_phang, suggest_recode
from .io_utils import _TEN_BO_QUA, group_columns
from .utils import LoiPhanTich, norm_value, to_numeric

Q = yaml.safe_load((Path(__file__).resolve().parents[2] / "giai-thich" / "chat-luong.yaml").read_text(encoding="utf-8"))
SO_CAU_LIKERT_TOI_THIEU = 5     # chọn một đáp án cho mọi câu chỉ đáng ngờ khi có từ ngần này câu
TY_LE_BO_TRONG = 0.5            # bỏ trống hơn một nửa số câu
SO_DONG_TOI_DA = 200            # số dòng liệt kê tối đa mỗi nhóm


def _row(i) -> int:
    return int(i) + 2


def _content_columns(df: pd.DataFrame) -> list[str]:
    """Cột câu trả lời: bỏ dấu thời gian, họ tên, email… (thông tin nhận dạng không tính khi so trùng)."""
    return [c for c in df.columns if not _TEN_BO_QUA.search(c)]


def likert_columns(df: pd.DataFrame) -> list[str]:
    """Các cột câu Likert: nhóm câu đánh số (từ 3 câu) mang số nguyên 0–10, hoặc chữ thuộc bộ nhãn Likert."""
    text = {c for g in suggest_recode(df) for c in g["cot"]}
    out = []
    for g in group_columns(list(df.columns)):
        if len(g["cot"]) < 3:
            continue
        for c in g["cot"]:
            v = to_numeric(df[c]).dropna()
            if c in text or (len(v) and v.notna().all() and (v == v.round()).all() and v.min() >= 0 and v.max() <= 10
                             and df[c].notna().sum() == len(v)):
                out.append(c)
    return list(dict.fromkeys(out))


def check(df: pd.DataFrame, p: dict | None = None) -> dict:
    """p: {"chu_y": {"cot": "CauKiemTra", "dung": "3"}} – câu kiểm tra sự chú ý (không bắt buộc)."""
    p = p or {}
    cols = _content_columns(df)
    nhom = []

    dup = df[cols].astype(str).duplicated(keep="first") if cols else pd.Series(False, index=df.index)
    nhom.append({"ma": "trung_lap", "dong": [_row(i) for i in df.index[dup]]})

    lik = likert_columns(df)
    straight = []
    if len(lik) >= SO_CAU_LIKERT_TOI_THIEU:
        block = df[lik].map(lambda v: v if pd.isna(v) else norm_value(v))
        answered = block.notna().sum(axis=1)
        same = block.nunique(axis=1, dropna=True) == 1
        straight = [_row(i) for i in df.index[same & (answered >= SO_CAU_LIKERT_TOI_THIEU)]]
    nhom.append({"ma": "mot_dap_an", "dong": straight, "so_cau": len(lik)})

    blank = df[cols].isna().mean(axis=1) > TY_LE_BO_TRONG if cols else pd.Series(False, index=df.index)
    nhom.append({"ma": "bo_trong", "dong": [_row(i) for i in df.index[blank]], "so_cau": len(cols)})

    cy = p.get("chu_y") or {}
    if cy.get("cot"):
        if cy["cot"] not in df.columns:
            raise LoiPhanTich(f"Không tìm thấy cột “{cy['cot']}” để làm câu kiểm tra sự chú ý.")
        dung = str(cy.get("dung", "")).strip()
        if not dung:
            raise LoiPhanTich("Hãy nhập đáp án đúng của câu kiểm tra sự chú ý.")
        s = df[cy["cot"]]
        # Đáp án dạng chữ Likert ("Đồng ý") được so như số nếu cột đang là chữ còn đáp án gõ là số
        table = {k: str(v) for k, v in _bang_phang("dong_y_5").items()}
        val = s.map(lambda v: None if pd.isna(v) else table.get(" ".join(str(v).lower().split()), norm_value(v)))
        want = table.get(" ".join(dung.lower().split()), norm_value(dung))
        sai = val.isna() | (val != want)
        nhom.append({"ma": "chu_y", "dong": [_row(i) for i in df.index[sai]], "cot": cy["cot"], "dung": dung})

    for g in nhom:
        g["so_phieu"] = len(g["dong"])
        g["dong"] = g["dong"][:SO_DONG_TOI_DA]
        txt = Q["nhom"][g["ma"]]
        g.update(ten=txt["ten"], ly_do_bao_cao=txt["ly_do_bao_cao"],
                 giai_thich=txt["giai_thich"].format(**{k: g.get(k, "") for k in ("so_cau", "cot", "dung")}))
    return {"n": len(df), "nhom": nhom, "cot_likert": len(lik), "gioi_thieu": Q["gioi_thieu"],
            "chu_y_huong_dan": Q["chu_y_huong_dan"], "khong_co": Q["khong_co"], "mau_bao_cao": Q["bao_cao"]}


def exclude(df: pd.DataFrame, rows) -> pd.DataFrame:
    """Loại các phiếu học sinh đã chọn (số dòng như Excel). Dòng không tồn tại thì bỏ qua."""
    if not rows:
        return df
    try:
        idx = {int(r) - 2 for r in rows}
    except (TypeError, ValueError) as e:
        raise LoiPhanTich("'loai_dong' phải là danh sách số dòng.") from e
    keep = [i for i in df.index if i not in idx]
    if not keep:
        raise LoiPhanTich("Đã loại hết mọi phiếu, không còn dữ liệu để phân tích.")
    return df.loc[keep]   # giữ chỉ số gốc để mọi cảnh báo vẫn báo đúng số dòng trong file
