"""Thử gọi Claude thật: chạy t-test trên dữ liệu mẫu rồi nhờ AI giải thích.
Cần đặt biến môi trường ANTHROPIC_API_KEY trước khi chạy.
Chạy: .venv\\Scripts\\python thu_giai_thich.py"""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
csv = Path(__file__).resolve().parents[1] / "sample-data" / "khao-sat-mau.csv"
params = {
    "analysis": "t-test", "type": "independent", "dv": "TT", "dv_label": "Hứng thú học tập",
    "group": "GioiTinh",
    "thang_do": [{"ma": "LIKERT", "gia_tri": {"min": 1, "max": 5},
                  "bien": [{"ma": "TT", "ten": "Hứng thú học tập", "cot": ["TT1", "TT2", "TT3", "TT4"], "dao": ["TT4"]}]}],
}
with csv.open("rb") as f:
    result = client.post("/phan-tich", files={"file": (csv.name, f, "text/csv")},
                         data={"params": json.dumps(params)}).json()

question = "Em không hiểu vì sao lại đọc dòng Welch. Kết quả này nghĩa là gì?"
r = client.post("/giai-thich", json={"ket_qua": result, "cau_hoi": question})
body = r.json()
if r.status_code != 200:
    print("Lỗi:", body)
else:
    print(body["tra_loi"])
    print("\n---", body["model"], body["usage"])
