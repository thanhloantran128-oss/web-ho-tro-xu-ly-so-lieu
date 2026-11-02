"""Giải thích kết quả tự động theo quy tắc – không dùng AI, không gửi dữ liệu ra ngoài.

Lời văn nằm trong thư mục giai-thich/*.yaml (sửa lời không cần sửa code).
Quy tắc quyết định (đọc dòng nào, ngưỡng nào) lấy từ bộ skill trong skills-hs/.
Định dạng số theo APA với dấu phẩy thập phân; p, r, α, η² bỏ số 0 đầu.

Đầu ra:
{
  "tom_tat":   [câu ngắn – lớp 1],
  "chi_tiet":  [{"tieu_de": ..., "noi_dung": [...]}] – lớp 2,
  "bao_cao":   "mẫu câu viết báo cáo theo APA",
  "canh_bao":  [...], "goi_mo": [...], "thuat_ngu": [...]
}
"""
from pathlib import Path

import yaml

from .scales import classify

ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = ROOT / "giai-thich"


def _load():
    lib = {f.stem: yaml.safe_load(f.read_text(encoding="utf-8")) for f in LIB_DIR.glob("*.yaml")}
    likert = yaml.safe_load((ROOT / "scales" / "likert-tu-xay-dung.yaml").read_text(encoding="utf-8"))
    return lib, likert


L, LIKERT = _load()
CHUNG = L["chung"]
CFG = CHUNG["dinh_dang"]
NG = CHUNG["nguong"]
ALPHA = NG["alpha"]


# ---------- Định dạng số ----------

def so(x, nd=None, bo0=False) -> str:
    """3.456 → '3,46'; −0.5 → '−0,50'; bo0=True: 0.061 → ',06' (chuẩn APA cho p, r, α, η²)."""
    if x is None:
        return "—"
    nd = CFG["so_le"] if nd is None else nd
    v = round(float(x), nd)
    if v == 0:
        v = 0.0
    s = f"{abs(v):.{nd}f}"
    if bo0 and CFG["bo_so_0_dau"] and s.startswith("0"):
        s = s[1:]
    s = s.replace(".", CFG["dau_thap_phan"])
    return (CFG["dau_am"] if v < 0 else "") + s


def so_gon(x) -> str:
    """Số nguyên thì không có phần lẻ (min, max, trung vị, giá trị kiểm định)."""
    if x is None:
        return "—"
    return so(x, 0) if float(x).is_integer() else so(x)


def p_txt(p) -> str:
    if p is None:
        return "= —"
    if p < 0.001:
        return "< " + so(0.001, 3, bo0=True)
    return "= " + so(p, CFG["so_le_p"], bo0=True)


def df_txt(df) -> str:
    if df is None:
        return "—"
    return str(int(round(df))) if abs(df - round(df)) < 1e-9 else so(df)


def pct(x) -> str:
    return so(x, 1) + "%"


def band(x, cuts, names):
    for c, n in zip(cuts, names):
        if x < c:
            return n
    return names[-1]


def _sec(key, lines):
    return {"tieu_de": CHUNG["tieu_de"][key], "noi_dung": [s for s in lines if s]}


def _cap(s: str) -> str:
    """Viết hoa chữ cái đầu câu (tên biến điền vào đầu câu thường là chữ thường)."""
    if not s or not s[0].isalpha() or "Ͱ" <= s[0] <= "Ͽ":  # không viết hoa ký hiệu Hy Lạp (η², α)
        return s
    return s[0].upper() + s[1:]


def _cau(s: str) -> str:
    """Câu cảnh báo lấy từ thư viện thang đo có thể thiếu dấu chấm cuối."""
    s = s.strip()
    return s if s.endswith((".", "!", "?")) else s + "."


def _out(analysis, tom_tat, chi_tiet, bao_cao, canh_bao, goi_mo, bo_thuat_ngu=()):
    chi_tiet = [{"tieu_de": s["tieu_de"], "noi_dung": [_cap(x) for x in s["noi_dung"]]}
                for s in chi_tiet if s["noi_dung"]]
    terms = [CHUNG["thuat_ngu"][k] for k in CHUNG["thuat_ngu_theo_phan_tich"].get(analysis, [])
             if k not in bo_thuat_ngu]
    return {"tom_tat": [_cap(s) for s in tom_tat if s], "chi_tiet": chi_tiet, "bao_cao": _cap(bao_cao),
            "canh_bao": [_cap(s) for s in canh_bao], "goi_mo": goi_mo, "thuat_ngu": terms}


def _d_line(T, d, v):
    if d is None:
        return T["muc_anh_huong"]["khong_co"]
    key = band(abs(d), NG["cohens_d"], ["rat_nho", "nho", "trung_binh", "lon"])
    return T["muc_anh_huong"][key].format(**v)


# ---------- t-test ----------

def _ttest(r):
    T = L["t-test"]
    kind = r["type"]
    row = r.get("dong_nen_doc", "student")
    st = r[row]
    sig = st["p"] is not None and st["p"] <= ALPHA
    d = r.get("cohens_d")
    g = r["groups"]
    v = {"ten_bien": r["dv"]["label"], "t": so(st["t"]), "df": df_txt(st["df"]), "p": p_txt(st["p"]),
         "d": so(abs(d)) if d is not None else "—", "chenh_lech": so(st["mean_diff"]),
         "ci_thap": so(st["ci95"][0]), "ci_cao": so(st["ci95"][1])}
    dk, canh_bao = [], []

    if kind == "independent":
        g1, g2 = g
        hi, lo = (g1, g2) if g1["mean"] >= g2["mean"] else (g2, g1)
        v.update(nhom_1=g1["label"], nhom_2=g2["label"], m_1=so(g1["mean"]), sd_1=so(g1["sd"]),
                 m_2=so(g2["mean"]), sd_2=so(g2["sd"]),
                 nhom_cao=hi["label"], m_cao=so(hi["mean"]), sd_cao=so(hi["sd"]), n_cao=hi["n"],
                 nhom_thap=lo["label"], m_thap=so(lo["mean"]), sd_thap=so(lo["sd"]), n_thap=lo["n"],
                 levene_p=p_txt(r["levene"]["p"]), levene_F=so(r["levene"]["F"]))
        dk.append(T["dieu_kien"]["levene_dong_nhat" if r["levene"]["p"] > ALPHA
                                 else "levene_khong_dong_nhat"].format(**v))
        checks = list(zip(g, r["normality"]["skewness_by_group"]))
    elif kind == "one-sample":
        g1 = g[0]
        mu = r["test_value"]
        v.update(m=so(g1["mean"]), sd=so(g1["sd"]), n=g1["n"], gia_tri_kd=so_gon(mu),
                 huong="cao hơn" if g1["mean"] > mu else "thấp hơn")
        checks = [(g1, r["normality"]["skewness_by_group"][0])]
    else:  # paired
        g1, g2 = g
        hi, lo = (g1, g2) if g1["mean"] >= g2["mean"] else (g2, g1)
        v.update(do_1=g1["label"], do_2=g2["label"], m_1=so(g1["mean"]), sd_1=so(g1["sd"]),
                 m_2=so(g2["mean"]), sd_2=so(g2["sd"]), n=g1["n"],
                 do_cao=hi["label"], m_cao=so(hi["mean"]), sd_cao=so(hi["sd"]),
                 do_thap=lo["label"], m_thap=so(lo["mean"]), sd_thap=so(lo["sd"]))
        checks = [({"label": "hiệu số giữa hai lần đo", "n": g1["n"]}, r["normality"]["skewness_of_diff"])]

    np_ = r.get("nonparametric") or {}
    ten_pt = np_.get("test", "kiểm định phi tham số")
    lech = False
    for grp, sk in checks:
        if sk is not None and abs(sk) >= NG["skewness"][0] and grp["n"] < NG["co_mau_on_dinh"]:
            dk.append(T["dieu_kien"]["lech_manh"].format(ten_nhom=grp["label"], skew=so(sk), n=grp["n"],
                                                         ten_kd_pt=ten_pt))
            lech = True
        if grp["n"] < NG["nhom_nho"]:
            canh_bao.append(T["dieu_kien"]["nhom_nho"].format(ten_nhom=grp["label"], n=grp["n"]))
    if not lech:
        dk.append(T["dieu_kien"]["phan_phoi_on"])

    ket = "co_y_nghia" if sig else "khong_y_nghia"
    kl = T["ket_luan"][kind][ket].format(**v)
    eff = _d_line(T, d, v)
    if sig and d is not None and abs(d) < NG["cohens_d"][0]:
        canh_bao.append(T["canh_bao"]["y_nghia_nhung_nho"])
    if np_.get("p") is not None and (np_["p"] <= ALPHA) != sig:
        canh_bao.append(T["canh_bao"]["khong_thong_nhat"].format(ten_kd_pt=ten_pt, p_pt=p_txt(np_["p"])))
    if kind == "independent" and sig:
        canh_bao.append(T["canh_bao"]["nhan_qua"])

    bao = T["bao_cao"][kind][ket].format(**v)
    if kind == "independent" and row == "welch":
        bao += T["bao_cao"]["independent"]["ghi_chu_welch"].format(**v)
    chi_tiet = [_sec("muc_dich", [T["muc_dich"][kind].format(**v)]), _sec("dieu_kien", dk),
                _sec("doc_ket_qua", [T["doc_ket_qua"][row].format(**v)]),
                _sec("muc_anh_huong", [eff]), _sec("ket_luan", [kl])]
    goi_mo = [s.format(**v) for s in T["goi_mo"][ket]]
    bo = () if kind == "independent" else ("levene", "welch")
    return _out("t-test", [kl, eff], chi_tiet, bao, canh_bao, goi_mo, bo)


# ---------- ANOVA ----------

def _anova(r):
    A = L["anova"]
    groups = {g["label"]: g for g in r["groups"]}
    lev_ok = r["levene"]["p"] > ALPHA
    main = r["anova"] if lev_ok else r["welch"]
    sig = bool(r["co_y_nghia_tong_the"])
    eta = r["anova"]["eta_sq"]
    v = {"ten_bien": r["dv"]["label"], "ten_nhom": r["factor"]["label"], "k": len(groups),
         "F": so(main["F"]), "df1": df_txt(main["df1"]), "df2": df_txt(main["df2"]), "p": p_txt(main["p"]),
         "eta": so(eta, bo0=True), "levene_p": p_txt(r["levene"]["p"]), "posthoc": r["posthoc"]["method"]}

    doc = [A["doc_ket_qua"]["anova" if lev_ok else "welch"].format(**v),
           A["doc_ket_qua"]["co_y_nghia" if sig else "khong_y_nghia"].format(**v)]
    canh_bao = list(r.get("canh_bao") or [])
    cap_bao_cao = []
    if sig:
        pairs = r["posthoc"]["pairs"]
        sig_pairs = [pp for pp in pairs if pp.get("p") is not None and pp["p"] <= ALPHA]
        for pp in sig_pairs:
            hi, lo = (pp["i"], pp["j"]) if pp["mean_diff"] > 0 else (pp["j"], pp["i"])
            pv = {"nhom_cao": hi, "m_cao": so(groups[hi]["mean"]), "sd_cao": so(groups[hi]["sd"]),
                  "nhom_thap": lo, "m_thap": so(groups[lo]["mean"]), "sd_thap": so(groups[lo]["sd"]),
                  "p_cap": p_txt(pp["p"])}
            doc.append(A["doc_ket_qua"]["cap_khac_biet"].format(**pv))
            cap_bao_cao.append(A["bao_cao"]["posthoc_cap"].format(**pv))
        if sig_pairs and len(sig_pairs) < len(pairs):
            doc.append(A["doc_ket_qua"]["cap_con_lai"])
        if not sig_pairs:
            canh_bao.append(A["canh_bao"]["tong_the_khong_cap"])
    kw = r.get("nonparametric") or {}
    if kw.get("p") is not None and (kw["p"] <= ALPHA) != sig:
        canh_bao.append(A["canh_bao"]["khong_thong_nhat"].format(H=so(kw["H"]), p_pt=p_txt(kw["p"])))
    if sig:
        canh_bao.append(A["canh_bao"]["nhan_qua"])

    eff = A["muc_anh_huong"][band(eta, NG["eta_sq"], ["rat_nho", "nho", "trung_binh", "lon"])].format(**v)
    ket = "co_y_nghia" if sig else "khong_y_nghia"
    kl = A["ket_luan"][ket].format(**v)
    bao = A["bao_cao"][ket + ("" if lev_ok else "_welch")].format(**v)
    if cap_bao_cao:
        bao += A["bao_cao"]["posthoc"].format(posthoc=v["posthoc"], cac_cap="; ".join(cap_bao_cao))
    dk = [A["dieu_kien"]["levene_dong_nhat" if lev_ok else "levene_khong_dong_nhat"].format(**v)]
    chi_tiet = [_sec("muc_dich", [A["muc_dich"].format(**v)]), _sec("dieu_kien", dk),
                _sec("doc_ket_qua", doc), _sec("muc_anh_huong", [eff]), _sec("ket_luan", [kl])]
    return _out("anova", [kl, eff], chi_tiet, bao, canh_bao, list(A["goi_mo"][ket]))


# ---------- Thống kê mô tả ----------

def _mo_ta(r):
    M = L["mo-ta"]
    doc, phan_phoi, canh_bao = [], [], []
    bao = [M["bao_cao"]["mo_dau"].format(N=r["n_total"])]
    for var in r["variables"]:
        ten = var["label"]
        if var["type"] in ("scale", "likert") and var.get("mean") is not None:
            v = {"ten": ten, "m": so(var["mean"]), "sd": so(var["sd"]), "mdn": so_gon(var["median"]),
                 "min": so_gon(var["min"]), "max": so_gon(var["max"])}
            doc.append(M["bien_dinh_luong"].format(**v))
            bao.append(M["bao_cao"]["dinh_luong"].format(**v))
            sk = var.get("skewness")
            if sk is not None:
                key = band(abs(sk), NG["skewness"], ["can_doi", "lech_vua", "lech_manh"])
                huong = M["huong_lech"]["phai" if sk > 0 else "trai"]
                phan_phoi.append(M["phan_phoi"][key].format(skew=so(sk), huong_lech=huong, **v))
            ku = var.get("kurtosis")
            if ku is not None and abs(ku) > NG["kurtosis"]:
                phan_phoi.append(M["phan_phoi"]["nhon"].format(kurt=so(ku), **v))
        elif var.get("tan_suat"):
            top = max(var["tan_suat"], key=lambda row: row["freq"])
            v = {"ten": ten, "nhom_nhieu_nhat": top["label"], "pct": pct(top["valid_percent"]), "n": top["freq"]}
            doc.append(M["bien_phan_loai"].format(**v))
            bao.append(M["bao_cao"]["phan_loai"].format(**v))
        total = var["n_valid"] + var["n_missing"]
        if total and var["n_missing"] / total > NG["thieu_du_lieu"]:
            canh_bao.append(M["canh_bao"]["thieu_nhieu"].format(ten=ten, n_thieu=var["n_missing"],
                                                                ty_le_thieu=pct(var["n_missing"] / total * 100)))
        if var.get("canh_bao"):
            canh_bao.append(M["canh_bao"]["khong_phai_so"].format(ten=ten, chi_tiet=var["canh_bao"]))
    tom = M["tom_tat"].format(N=r["n_total"], so_bien=len(r["variables"]))
    chi_tiet = [_sec("muc_dich", [M["muc_dich"]]), _sec("doc_ket_qua", doc), _sec("phan_phoi", phan_phoi)]
    return _out("mo-ta", [tom] + doc[:3], chi_tiet, " ".join(bao), canh_bao, list(M["goi_mo"]))


# ---------- Tần suất ----------

def _tan_suat(r):
    S = L["tan-suat"]
    rows = sorted(r["table"], key=lambda row: -row["freq"])
    multi = r.get("multiple_response")
    v = {"ten": r.get("label") or r["variable"], "n_valid": r["n_valid"], "n_total": r["n_total"],
         "n_thieu": r["n_missing"]}
    if rows:
        v.update(nhom_1=rows[0]["label"], pct_1=pct(rows[0]["valid_percent"]), n_1=rows[0]["freq"])
    if len(rows) > 1:
        v.update(nhom_2=rows[1]["label"], pct_2=pct(rows[1]["valid_percent"]), n_2=rows[1]["freq"])
    key = "hai_nhom" if len(rows) > 1 else "mot_nhom"
    doc = []
    if multi:
        doc.append(S["doc_bang"]["nhieu_lua_chon"].format(**v))
    else:
        doc.append(S["doc_bang"]["co_thieu" if r["n_missing"] else "khong_thieu"].format(**v))
        if r["type"] in ("ordinal", "likert"):
            doc.append(S["doc_bang"]["tich_luy"])
    canh_bao = []
    if r.get("nhom_nho_duoi_5"):
        canh_bao.append(S["canh_bao"]["nhom_nho"].format(cac_nhom_nho=", ".join(map(str, r["nhom_nho_duoi_5"]))))
    tom = S["tom_tat"][key].format(**v) if rows else ""
    bao = S["bao_cao"][key].format(**v) if rows else ""
    if r["n_missing"] and not multi:
        bao += S["bao_cao"]["thieu"].format(**v)
    chi_tiet = [_sec("muc_dich", [S["muc_dich"]]), _sec("doc_ket_qua", doc + [tom])]
    return _out("tan-suat", [tom], chi_tiet, bao, canh_bao, list(S["goi_mo"]))


# ---------- Trung bình – độ lệch chuẩn ----------

def _likert_bands(points):
    return LIKERT.get(f"phan_loai_{points}_muc") if points in (5, 7) else None


def _trung_binh(r):
    B = L["trung-binh"]
    sp = r.get("scale_points")
    bands = _likert_bands(sp)
    doc, phan_tan, bao = [], [], []
    items = [dict(x) for x in r["variables"]]
    comp = r.get("composite")
    for var in items + ([{"name": comp["name"], "label": comp.get("label") or comp["name"], **comp, "_tong": True}]
                        if comp else []):
        if var.get("mean") is None:
            continue
        v = {"ten": var.get("label") or var["name"], "m": so(var["mean"]), "sd": so(var["sd"]), "n": var["n"],
             "so_muc": sp}
        if var.get("_tong"):
            doc.append(B["bien_tong_hop"].format(n_loai=var.get("n_bi_loai_do_thieu", 0), **v))
        else:
            doc.append(B["bien"].format(**v))
        muc = classify(var["mean"], bands) if bands else None
        if muc:
            doc.append(B["muc_likert"].format(muc_likert=muc, **v))
            bao.append(B["bao_cao"].format(muc=muc.lower(), **v))
        else:
            bao.append(B["bao_cao_khong_muc"].format(**v))
        if sp == 5 and var.get("sd") is not None:
            # Gợi ý diễn giải cho thang Likert 5 mức (skill trung-binh-do-lech-chuan)
            key = "dong_nhat" if var["sd"] < 0.6 else "chia_re" if var["sd"] > 1.2 else "vua"
            phan_tan.append(B["do_phan_tan"][key].format(**v))
    canh_bao = []
    if len(doc) > 1:
        canh_bao.append(B["canh_bao"]["khong_phai_kiem_dinh"])
    if bands:
        canh_bao.append(B["canh_bao"]["muon_so_voi_trung_lap"])
    chi_tiet = [_sec("muc_dich", [B["muc_dich"]]), _sec("doc_ket_qua", doc), _sec("phan_phoi", phan_tan)]
    return _out("trung-binh", doc[:4], chi_tiet, " ".join(bao), canh_bao, list(B["goi_mo"]))


# ---------- Thang đo ----------

def _thang_do(r):
    D = L["thang-do"]
    tom, chi_tiet, bao, canh_bao = [], [], [], []
    for rep in r["ket_qua_thang_do"]:
        sc = rep["scale"]
        ten_thang = sc.get("ten_viet") or sc["ma"]
        ten_giua_cau = ten_thang[:1].lower() + ten_thang[1:]  # "Thang đo…" đứng giữa câu
        kt = rep.get("kiem_tra") or {}
        if rep["trang_thai"] == "can_xac_nhan":
            lech = kt["lech_ma_hoa"]
            line = D["trang_thai"]["can_xac_nhan"].format(
                khoang_quan_sat=f"[{so_gon(lech['khoang_quan_sat'][0])}; {so_gon(lech['khoang_quan_sat'][1])}]",
                khoang_thang=f"[{so_gon(lech['khoang_cua_thang'][0])}; {so_gon(lech['khoang_cua_thang'][1])}]",
                goi_y_tru=lech["goi_y_tru"])
            tom.append(line)
            chi_tiet.append({"tieu_de": ten_thang, "noi_dung": [line]})
            continue
        if rep["trang_thai"] == "loi_du_lieu":
            lines = [D["trang_thai"]["loi_du_lieu"]]
            for loai, key in (("ngoai_khoang", "loi_ngoai_khoang"), ("khong_phai_so", "loi_khong_phai_so"),
                              ("khong_nguyen", "loi_khong_nguyen")):
                for cot, dong in (kt.get(loai) or {}).items():
                    lines.append(D["trang_thai"][key].format(cot=cot, dong=", ".join(map(str, dong))))
            tom.append(lines[0])
            chi_tiet.append({"tieu_de": ten_thang, "noi_dung": lines})
            continue

        likert = sc["ma"] == "LIKERT"
        lines = [D["muc_dich_likert"] if likert else D["muc_dich"].format(ten_thang=ten_giua_cau)]
        alphas = kt.get("cronbach") or {}
        for code, kq in rep["ket_qua"].items():
            if sc["ma"] == "LIKERT":
                ten_diem = kq["ten"]
            elif code == "TONG":
                ten_diem = f"{sc['ma']} – điểm tổng"
            else:
                ten_diem = f"{sc['ma']} – {kq['ten']}"
            v = {"ten_diem": ten_diem, "m": so(kq["mean"]), "sd": so(kq["sd"]), "n": kq["n"],
                 "ten_thang": ten_giua_cau, "tac_gia": sc.get("tac_gia") or ""}
            line = D["diem"].format(**v)
            lines.append(line)
            tom.append(line)
            n_loai = (kt.get("n_bi_loai_do_thieu") or {}).get(code, 0)
            if n_loai:
                lines.append(D["bi_loai"].format(n_loai=n_loai, **v))
            a = alphas.get(code)
            if a is not None:
                key = band(a, NG["cronbach"], ["chua_dat", "chap_nhan", "tot", "rat_tot"])  # < ,6 / ,6–,7 / ,7–,9 / ≥ ,9
                lines.append(D["do_tin_cay"][key].format(alpha=so(a, bo0=True), **v))
                if sc["ma"] == "LIKERT":
                    bao.append(D["bao_cao"]["ket_qua"].format(**v) + f" Cronbach's α = {so(a, bo0=True)}.")
                else:
                    bao.append(D["bao_cao"]["phuong_phap"].format(alpha=so(a, bo0=True), **v))
                if key == "chua_dat":
                    canh_bao.append(D["do_tin_cay"][key].format(alpha=so(a, bo0=True), **v))
            elif code in (kt.get("tuong_quan_2_cau") or {}):
                lines.append(D["do_tin_cay"]["hai_cau"].format(r=so(kt["tuong_quan_2_cau"][code], bo0=True), **v))
            neg = (kt.get("tuong_quan_bien_tong_am") or {}).get(code)
            if neg:
                w = D["do_tin_cay"]["tuong_quan_am"].format(cac_cau=", ".join(neg), **v)
                lines.append(w)
                canh_bao.append(w)
            items = (kt.get("thong_ke_cau") or {}).get(code) or []
            thap = [i["cot"] for i in items if i["tuong_quan_bien_tong"] is not None
                    and 0 <= i["tuong_quan_bien_tong"] < NG["tuong_quan_bien_tong"]]
            if thap:
                lines.append(D["do_tin_cay"]["tuong_quan_thap"].format(cac_cau=", ".join(thap), **v))
            tang = [i for i in items if a is not None and i["alpha_neu_loai"] is not None and i["alpha_neu_loai"] > a]
            if tang:
                w = D["do_tin_cay"]["loai_cau"].format(
                    cac_cau=", ".join(i["cot"] for i in tang), alpha=so(a, bo0=True),
                    alpha_moi=so(max(i["alpha_neu_loai"] for i in tang), bo0=True), **v)
                lines.append(w)
                if key in ("chua_dat", "chap_nhan"):  # α đã tốt thì chỉ ghi ở phần chi tiết
                    canh_bao.append(w)
            if kq.get("phan_bo_muc"):
                lines.append(D["phan_bo"].format(
                    cac_muc="; ".join(f"{k}: {pct(x)}" for k, x in kq["phan_bo_muc"].items())))
            if sc["ma"] != "LIKERT":
                bao.append(D["bao_cao"]["ket_qua"].format(**v))
        loai = sc.get("loai_nguong") or ("quy_uoc" if sc["ma"] == "LIKERT" else None)
        if loai in D["loai_nguong"]:
            lines.append(D["loai_nguong"][loai].format(nguon_nguong=sc.get("nguon_phan_loai") or ""))
        if sc.get("nhay_cam"):
            lines.append(D["nhay_cam"])
        if not likert:  # cảnh báo của mẫu Likert là hướng dẫn cho người soạn thư viện, không cho học sinh
            canh_bao += [_cau(s) for s in sc.get("canh_bao") or []]
        chi_tiet.append({"tieu_de": "Thang Likert tự xây dựng" if likert else ten_thang, "noi_dung": lines})
    return _out("thang-do", tom, chi_tiet, " ".join(bao), canh_bao, list(D["goi_mo"]))


# ---------- Câu nhiều lựa chọn ----------

def _nhieu_lua_chon(r):
    N = L["nhieu-lua-chon"]
    rows = [x for x in r["table"] if x["freq"] > 0]
    top = [x for x in rows if not x.get("la_khac")][:3]
    v = {"ten": r["label"], "n_tra_loi": r["n_tra_loi"], "n_khong_tra_loi": r["n_khong_tra_loi"],
         "tong_luot": r["tong_luot_chon"], "tb_lua_chon": so(r["so_lua_chon_tb"], 1),
         "so_khac": r["so_cau_tra_loi_khac"], "so_khong_chon": r["so_nguoi_khong_chon_gi"]}
    for i, x in enumerate(top, 1):
        v.update({f"lua_chon_{i}": x["label"], f"pct_{i}": pct(x["pct_nguoi"]), f"n_{i}": x["freq"]})

    doc = [N["doc_ket_qua"]["hai_loai_pct"].format(**v), N["doc_ket_qua"]["trung_binh_lua_chon"].format(**v)]
    if r["n_khong_tra_loi"]:
        doc.append(N["doc_ket_qua"]["khong_tra_loi"].format(**v))
    if r["so_nguoi_khong_chon_gi"]:
        doc.append(N["doc_ket_qua"]["khong_chon_gi"].format(**v))
    if r["so_cau_tra_loi_khac"]:
        doc.append(N["doc_ket_qua"]["khac"].format(**v))
    tom = N["tom_tat"][{1: "mot", 2: "hai", 3: "ba"}[len(top)]].format(**v) if top else ""
    bao = ""
    if top:
        bao = N["bao_cao"]["mo_ta"].format(**v)
        if len(top) > 1:
            bao += N["bao_cao"]["tiep_2"].format(**v)
        if len(top) > 2:
            bao += N["bao_cao"]["tiep_3"].format(**v)
        bao += N["bao_cao"]["ket"].format(**v)
    canh_bao = list(r.get("canh_bao") or []) + [N["canh_bao"]["khong_dung_pct_luot"], N["canh_bao"]["bieu_do"]]

    chi_tiet = [_sec("muc_dich", [N["muc_dich"]]), _sec("doc_ket_qua", doc + [tom])]
    comp = r.get("so_sanh_nhom")
    if comp:
        names = [g["label"] for g in comp["cac_nhom"]]
        cv = {"nhom": comp["nhom"], "so_lan": comp["so_lan_kiem_dinh"]}
        lines = [N["so_sanh"]["muc_dich"].format(**cv)]
        if comp["so_lan_kiem_dinh"] > 1:
            lines.append(N["so_sanh"]["bonferroni"].format(**cv))
        any_sig = False
        for x in comp["theo_lua_chon"]:
            if x["p"] is None:
                continue
            xv = {**cv, "lua_chon": x["label"], "kiem_dinh": x["kiem_dinh"], "chi2": so(x["chi2"]),
                  "df": df_txt(x["df"]), "p": p_txt(x["p"]), "p_bon": p_txt(x["p_bonferroni"]),
                  "v": so(x["cramers_v"], bo0=True),
                  "cac_ty_le": "; ".join(f"{n}: {pct(t)}" for n, t in zip(names, x["pct_theo_nhom"]))}
            if x["p"] <= ALPHA and x["p_bonferroni"] <= ALPHA:
                lines.append(N["so_sanh"]["co_y_nghia"].format(**xv))
                key = "so_sanh_fisher" if x["kiem_dinh"] == "Fisher's exact" else "so_sanh"
                bao += N["bao_cao"][key].format(**xv)
                any_sig = True
            elif x["p"] <= ALPHA:
                lines.append(N["so_sanh"]["chi_y_nghia_truoc_hieu_chinh"].format(**xv))
                any_sig = True
            if x.get("o_ky_vong_nho"):
                canh_bao.append(N["so_sanh"]["o_ky_vong_nho"].format(**xv))
        lines.append(N["so_sanh"]["khong_y_nghia" if any_sig else "khong_lua_chon_nao"].format(**cv))
        chi_tiet.append({"tieu_de": f"So sánh theo {comp['nhom']}", "noi_dung": lines})
    return _out("nhieu-lua-chon", [tom, v["tb_lua_chon"] and N["doc_ket_qua"]["trung_binh_lua_chon"].format(**v)],
                chi_tiet, bao, canh_bao, list(N["goi_mo"]),
                () if comp else ("chi2", "fisher", "cramer", "bonferroni"))


# ---------- Bảng chéo – Chi-square ----------

# Mốc Cramér's V nhỏ / trung bình / lớn theo bậc tự do min(hàng, cột) − 1 (Cohen, 1988)
MOC_CRAMER = {1: [0.10, 0.30, 0.50], 2: [0.07, 0.21, 0.35], 3: [0.06, 0.17, 0.29]}


def _bang_cheo(r):
    B = L["bang-cheo"]
    use_fisher = r["kiem_dinh_nen_doc"] == "fisher"
    p_main = r["fisher_p"] if use_fisher else r["p"]
    sig = p_main is not None and p_main <= ALPHA
    v = r["cramers_v"] or 0
    muc = band(v, MOC_CRAMER.get(r["df_v"], [0.05, 0.15, 0.25]), ["rat_yeu", "yeu", "trung_binh", "manh"])
    vals = {"hang": r["hang"]["label"], "cot": r["cot"]["label"], "n": r["n"], "chi2": so(r["chi2"]), "df": r["df"],
            "p": p_txt(r["p"]), "p_fisher": p_txt(r["fisher_p"]), "v": so(v, bo0=True), "muc": B["muc"][muc],
            "pct_kv": so(r["pct_o_ky_vong_nho"], 1), "min_kv": so(r["ky_vong_nho_nhat"])}
    # Nhóm cột có tỷ lệ chênh nhiều nhất giữa các hàng
    row_pct = r["pct_hang"]
    spreads = [max(row[j] for row in row_pct) - min(row[j] for row in row_pct) for j in range(len(r["cot"]["nhom"]))]
    j = spreads.index(max(spreads))
    col_vals = [row[j] for row in row_pct]
    hi, lo = col_vals.index(max(col_vals)), col_vals.index(min(col_vals))
    vals.update(cot_muc=r["cot"]["nhom"][j], hang_cao=r["hang"]["nhom"][hi], hang_thap=r["hang"]["nhom"][lo],
                pct_cao=pct(max(col_vals)), pct_thap=pct(min(col_vals)))

    if use_fisher:
        dk = B["dieu_kien"]["ky_vong_nho_2x2"]
    elif r["pct_o_ky_vong_nho"] > 20:
        dk = B["dieu_kien"]["ky_vong_nho"]
    elif r["pct_o_ky_vong_nho"] > 0:
        dk = B["dieu_kien"]["ky_vong_hoi_nho"]
    else:
        dk = B["dieu_kien"]["ky_vong_on"]
    doc = [B["doc_ket_qua"]["fisher" if use_fisher else "chi2"].format(**vals), B["doc_ket_qua"]["phan_tram"].format(**vals)]
    if sig:
        doc.append(B["doc_ket_qua"]["chenh_lech"].format(**vals))
    ket = "co_y_nghia" if sig else "khong_y_nghia"
    kl = B["ket_luan"][ket].format(**{**vals, "p": p_txt(p_main)})
    eff = B["muc_anh_huong"].format(**vals)
    bao = B["bao_cao"][ket + ("_fisher" if use_fisher else "")].format(**vals)
    if sig:
        bao += B["bao_cao"]["chenh_lech"].format(**vals)
    canh_bao = [B["dieu_kien"]["ky_vong_nho"].format(**vals)] if (not use_fisher and r["pct_o_ky_vong_nho"] > 20) else []
    if sig:
        canh_bao.append(B["canh_bao"]["nhan_qua"])
    chi_tiet = [_sec("muc_dich", [B["muc_dich"].format(**vals)]), _sec("dieu_kien", [dk.format(**vals)]),
                _sec("doc_ket_qua", doc), _sec("muc_anh_huong", [eff]), _sec("ket_luan", [kl])]
    return _out("bang-cheo", [kl, eff if sig else ""], chi_tiet, bao, canh_bao,
                [s.format(**vals) for s in B["goi_mo"][ket]], () if use_fisher else ("fisher",))


# ---------- Tương quan ----------

def _tuong_quan(r):
    T = L["tuong-quan"]
    sp = r["phuong_phap"] == "spearman"
    base = {"ky_hieu": "*r*ₛ" if sp else "*r*", "ten_pp": "Spearman" if sp else "Pearson"}
    lines, bao, canh_bao, sig_pairs = [], [], [], []
    for c in r["cap"]:
        if c["r"] is None:
            continue
        sig = c["p"] <= ALPHA
        muc = band(abs(c["r"]), [0.1, 0.3, 0.5], ["rat_yeu", "yeu", "trung_binh", "manh"])
        v = {**base, "x": c["x_label"], "y": c["y_label"], "r": so(c["r"], bo0=True), "p": p_txt(c["p"]),
             "n": c["n"], "df": c["df"], "huong": T["huong"]["thuan" if c["r"] > 0 else "nghich"], "muc": T["muc"][muc],
             "y_nghia": T["doc_ket_qua"]["co_y_nghia" if sig else "khong_y_nghia"]}
        line = T["doc_ket_qua"]["cap"].format(**v)
        if c.get("ci95"):
            line += T["doc_ket_qua"]["ci"].format(ci=f"{so(c['ci95'][0], bo0=True)}; {so(c['ci95'][1], bo0=True)}")
        lines.append((abs(c["r"]) if sig else -1, line))
        if sig:
            sig_pairs.append(c)
            if muc == "rat_yeu":
                canh_bao.append(T["canh_bao"]["y_nghia_nhung_yeu"].format(**v))
        if sig or len(r["cap"]) <= 3:
            bao.append(T["bao_cao"]["co_y_nghia" if sig else "khong_y_nghia"].format(**v))
    m = len(lines)
    tom = []
    if m == 1:
        tom = [lines[0][1]]
    elif m > 1:
        tom = [T["tom_tat"]["nhieu_cap"].format(so_cap=m, so_cap_y_nghia=len(sig_pairs)), max(lines)[1]]
    doc = [T["phuong_phap"]["spearman" if sp else "pearson"], T["doc_ket_qua"]["doc_dau"]] + [l for _, l in lines]
    if m > 1:
        doc.append(T["doc_ket_qua"]["bonferroni"].format(so_cap=m))
    if sig_pairs:
        canh_bao.append(T["canh_bao"]["nhan_qua"])
    chi_tiet = [_sec("muc_dich", [T["muc_dich"]]), _sec("doc_ket_qua", doc)]
    goi = T["goi_mo"]["co_y_nghia" if sig_pairs else "khong_y_nghia"]
    return _out("tuong-quan", tom, chi_tiet, " ".join(bao), canh_bao, list(goi),
                ("pearson",) if sp else ("spearman",))


_HANDLERS = {"t-test": _ttest, "anova": _anova, "mo-ta": _mo_ta, "tan-suat": _tan_suat,
             "trung-binh": _trung_binh, "thang-do": _thang_do, "nhieu-lua-chon": _nhieu_lua_chon,
             "bang-cheo": _bang_cheo, "tuong-quan": _tuong_quan}


def giai_thich(result: dict) -> dict:
    return _HANDLERS[result["analysis"]](result)
