"""Chạy các phép phân tích trên dữ liệu mẫu và xuất lời giải thích tự động ra file Markdown để duyệt lời văn.
Chạy: .venv\\Scripts\\python tao_vi_du_giai_thich.py  →  ../giai-thich/VI_DU.md"""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)
CSV = ROOT / "sample-data" / "khao-sat-mau.csv"
PSS = {"ma": "PSS-10", "cot": [f"PSS{i}" for i in range(1, 11)]}
TT = {"ma": "LIKERT", "gia_tri": {"min": 1, "max": 5},
      "bien": [{"ma": "TT", "ten": "Hứng thú học tập", "cot": ["TT1", "TT2", "TT3", "TT4"], "dao": ["TT4"]}]}

CASES = [
    ("Thống kê mô tả", {"analysis": "mo-ta", "variables": [
        {"name": "GioiTinh", "label": "Giới tính", "type": "nominal"},
        {"name": "PSS3", "label": "Câu PSS3", "type": "likert"}]}),
    ("Tần suất – khối lớp", {"analysis": "tan-suat", "variable": "Khoi", "label": "Khối lớp", "type": "ordinal"}),
    ("Trung bình – độ lệch chuẩn", {"analysis": "trung-binh", "scale_points": 5,
                                    "variables": [{"name": "TT1", "label": "TT1"}, {"name": "TT3", "label": "TT3"}],
                                    "composite": {"name": "TT", "label": "Hứng thú học tập", "cot": ["TT1", "TT2", "TT3"]}}),
    ("Chấm điểm thang đo PSS-10 và Hứng thú học tập", {"analysis": "thang-do", "thang_do": [PSS, TT]}),
    ("Independent t-test – Hứng thú học tập theo giới tính", {"analysis": "t-test", "type": "independent", "dv": "TT",
                                                     "dv_label": "hứng thú học tập", "group": "GioiTinh",
                                                     "thang_do": [TT]}),
    ("One-sample t-test – Hứng thú học tập so với mức trung lập 3", {"analysis": "t-test", "type": "one-sample", "dv": "TT",
                                                            "dv_label": "hứng thú học tập", "test_value": 3,
                                                            "thang_do": [TT]}),
    ("Câu nhiều lựa chọn – Kênh tìm thông tin học tập, so sánh theo giới tính",
     {"analysis": "nhieu-lua-chon", "dang": "van_ban", "cot": "KenhThongTin",
      "label": "Kênh tìm thông tin học tập",
      "cac_lua_chon": ["Facebook", "TikTok", "Website, báo điện tử", "Bạn bè, người thân", "YouTube"],
      "nhom": "GioiTinh", "nhom_label": "giới tính"}),
    ("ANOVA – Căng thẳng theo khối", {"analysis": "anova", "dv": "PSS-10_TONG", "dv_label": "mức căng thẳng (PSS-10)",
                                      "factor": "Khoi", "factor_label": "khối lớp", "thang_do": [PSS]}),
]


def render(title, g):
    out = [f"## {title}", "", "### Lớp 1 – Tóm tắt", ""]
    out += [f"- {s}" for s in g["tom_tat"]]
    out += ["", "### Lớp 2 – Chi tiết", ""]
    for sec in g["chi_tiet"]:
        out += [f"**{sec['tieu_de']}**", ""] + [f"- {s}" for s in sec["noi_dung"]] + [""]
    if g["canh_bao"]:
        out += ["**Lưu ý**", ""] + [f"- {s}" for s in g["canh_bao"]] + [""]
    out += ["**Mẫu câu báo cáo (APA)**", "", f"> {g['bao_cao']}", "", "**Câu hỏi gợi mở**", ""]
    out += [f"- {s}" for s in g["goi_mo"]] + ["", "**Thuật ngữ**", ""] + [f"- {s}" for s in g["thuat_ngu"]]
    return "\n".join(out) + "\n"


parts = ["# Ví dụ lời giải thích tự động", "",
         "Sinh tự động từ dữ liệu MÔ PHỎNG `sample-data/khao-sat-mau.csv`. Sửa lời văn trong các file `.yaml` "
         "cùng thư mục rồi chạy lại `stats-api/tao_vi_du_giai_thich.py` để xem kết quả.", ""]
for title, params in CASES:
    with CSV.open("rb") as f:
        r = client.post("/phan-tich", files={"file": (CSV.name, f, "text/csv")}, data={"params": json.dumps(params)})
    r.raise_for_status()
    parts.append(render(title, r.json()["giai_thich"]))

target = ROOT / "giai-thich" / "VI_DU.md"
target.write_text("\n".join(parts), encoding="utf-8")
print(f"Đã ghi {target}")
