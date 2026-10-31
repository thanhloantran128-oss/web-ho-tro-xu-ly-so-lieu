"""Câu hỏi nhiều lựa chọn (Multiple Response). Đầu ra khớp skills-hs/nhieu-lua-chon.

Hai dạng dữ liệu:
- van_ban: một cột chứa các lựa chọn nối bằng dấu phẩy (Google Forms, Microsoft Forms).
- nhi_phan: mỗi lựa chọn một cột, 1 = có chọn.
"""
import math
import re

import numpy as np
import pandas as pd
from scipy import stats

from .ttest import _order
from .utils import LoiPhanTich, label_of, norm_value, require_column, to_numeric

NHAN_KHAC = "Khác"
NHOM_NHO = 5


def _split_text(series: pd.Series, known: list[str], sep: str) -> tuple[pd.DataFrame, int]:
    """Tách văn bản gộp thành bảng chọn/không chọn. Khi có danh sách lựa chọn gốc, tìm đúng từng lựa chọn
    (kể cả lựa chọn có dấu phẩy bên trong); phần chữ còn lại gom vào 'Khác'."""
    rows, n_khac = [], 0
    patterns = [(opt, re.compile(rf"(^|{re.escape(sep)})\s*{re.escape(opt)}\s*(?={re.escape(sep)}|$)"))
                for opt in sorted(known, key=len, reverse=True)]
    for text in series:
        chosen, rest = set(), str(text)
        for opt, pat in patterns:
            if pat.search(rest):
                chosen.add(opt)
                rest = pat.sub(sep, rest)
        leftovers = [t.strip() for t in rest.split(sep) if t.strip()]
        if known:
            if leftovers:
                chosen.add(NHAN_KHAC)
                n_khac += 1
        else:
            chosen |= set(leftovers)
        rows.append({c: True for c in chosen})
    ind = pd.DataFrame(rows, index=series.index).notna()  # ô có True = có chọn, ô trống = không chọn
    return ind, n_khac


def _indicators(df: pd.DataFrame, p: dict) -> tuple[pd.DataFrame, pd.Series, int, list]:
    dang = p.get("dang")
    if dang == "van_ban":
        col = p.get("cot")
        require_column(df, col)
        s = df[col]
        answered = s.notna() & s.astype(str).str.strip().ne("")
        known = [str(x).strip() for x in (p.get("cac_lua_chon") or []) if str(x).strip()]
        ind, n_khac = _split_text(s[answered], known, p.get("dau_phan_cach", ","))
        ind = ind.reindex(df.index, fill_value=False)
        order = known + ([NHAN_KHAC] if NHAN_KHAC in ind.columns and NHAN_KHAC not in known else [])
        order += [c for c in ind.columns if c not in order]
        return ind.reindex(columns=order, fill_value=False), answered, n_khac, order
    if dang == "nhi_phan":
        options = p.get("cot_lua_chon") or []
        if not options:
            raise LoiPhanTich("Dạng nhị phân cần danh sách 'cot_lua_chon' (mỗi lựa chọn một cột).")
        cols = [o["cot"] for o in options]
        for c in cols:
            require_column(df, c)
        block = df[cols].apply(to_numeric)
        answered = block.notna().any(axis=1)
        chosen_value = p.get("gia_tri_chon", 1)
        labels = [o.get("label", o["cot"]) for o in options]
        ind = pd.DataFrame({lab: (block[c] == chosen_value) for lab, c in zip(labels, cols)}, index=df.index)
        return ind, answered, 0, labels
    raise LoiPhanTich("Chọn dạng dữ liệu: 'van_ban' (một cột nối bằng dấu phẩy) hoặc 'nhi_phan' (mỗi lựa chọn một cột).")


def _compare(ind: pd.DataFrame, answered: pd.Series, group: pd.Series, labels: dict | None) -> dict:
    g = group.map(norm_value)
    valid = answered & g.notna()
    levels = sorted(g[valid].unique(), key=_order)
    if len(levels) < 2:
        raise LoiPhanTich("Biến nhóm cần ít nhất 2 nhóm có người trả lời.")
    sizes = [int((valid & (g == lv)).sum()) for lv in levels]
    tested = []
    # "Khác" gom nhiều câu tự ghi khác nhau nên không so sánh giữa các nhóm
    for opt in [c for c in ind.columns if c != NHAN_KHAC]:
        chosen = [int((valid & (g == lv) & ind[opt]).sum()) for lv in levels]
        table = np.array([[c, n - c] for c, n in zip(chosen, sizes)])
        row = {"label": opt, "pct_theo_nhom": [c / n * 100 if n else None for c, n in zip(chosen, sizes)],
               "kiem_dinh": None, "chi2": None, "df": None, "p": None, "cramers_v": None, "o_ky_vong_nho": None}
        if table[:, 0].sum() == 0 or table[:, 1].sum() == 0:
            row["ghi_chu"] = "Không kiểm định được vì mọi người đều chọn hoặc đều không chọn."
            tested.append(row)
            continue
        chi2, pval, dof, expected = stats.chi2_contingency(table, correction=False)
        n = table.sum()
        row.update(chi2=chi2, df=dof, p=pval, cramers_v=math.sqrt(chi2 / n), kiem_dinh="Chi-square")
        if len(levels) == 2 and (expected < 5).any():
            # Fisher's exact dành riêng cho ô kỳ vọng nhỏ nên không cần cảnh báo thêm
            row.update(kiem_dinh="Fisher's exact", p=stats.fisher_exact(table).pvalue, o_ky_vong_nho=False)
        else:
            row["o_ky_vong_nho"] = bool((expected < 5).mean() > 0.2)
        tested.append(row)
    m = sum(1 for r in tested if r["p"] is not None)
    for r in tested:
        r["p_bonferroni"] = min(1.0, r["p"] * m) if r["p"] is not None else None
    return {"cac_nhom": [{"label": label_of(lv, labels), "n": n} for lv, n in zip(levels, sizes)],
            "so_lan_kiem_dinh": m, "theo_lua_chon": tested}


def run(df: pd.DataFrame, p: dict, value_labels: dict) -> dict:
    """p: {label?, dang, cot?, cac_lua_chon?, dau_phan_cach?, cot_lua_chon?, gia_tri_chon?, nhom?, nhom_label?}"""
    ind, answered, n_khac, order = _indicators(df, p)
    n_resp = int(answered.sum())
    if n_resp == 0:
        raise LoiPhanTich("Không có ai trả lời câu hỏi này.")
    freq = ind[answered].sum()
    total = int(freq.sum())
    table = []
    for opt in order:
        f = int(freq.get(opt, 0))
        table.append({"label": opt, "freq": f, "pct_nguoi": f / n_resp * 100,
                      "pct_luot": f / total * 100 if total else None, "la_khac": opt == NHAN_KHAC})
    # Sắp xếp từ nhiều đến ít; "Khác" luôn đứng cuối
    table.sort(key=lambda r: (r["la_khac"], -r["freq"]))
    result = {
        "analysis": "nhieu-lua-chon", "label": p.get("label") or p.get("cot") or "Câu nhiều lựa chọn",
        "dang": p["dang"], "n_total": len(df), "n_tra_loi": n_resp, "n_khong_tra_loi": len(df) - n_resp,
        "tong_luot_chon": total, "so_lua_chon_tb": total / n_resp,
        "so_nguoi_khong_chon_gi": int((answered & ~ind.any(axis=1)).sum()),
        "table": table, "so_cau_tra_loi_khac": n_khac,
        "lua_chon_it_nguoi": [r["label"] for r in table if r["freq"] < NHOM_NHO],
        "canh_bao": [],
    }
    if p.get("dang") == "van_ban" and not p.get("cac_lua_chon"):
        result["canh_bao"].append("Chưa khai báo danh sách lựa chọn gốc: lựa chọn có dấu phẩy bên trong có thể bị tách sai.")
    if p.get("nhom"):
        require_column(df, p["nhom"])
        comp = _compare(ind, answered, df[p["nhom"]], value_labels.get(p["nhom"]))
        comp["nhom"] = p.get("nhom_label", p["nhom"])
        for gr in comp["cac_nhom"]:
            if gr["n"] < NHOM_NHO:
                result["canh_bao"].append(f"Nhóm '{gr['label']}' chỉ có {gr['n']} người trả lời; nên gộp nhóm.")
        result["so_sanh_nhom"] = comp
    return result
