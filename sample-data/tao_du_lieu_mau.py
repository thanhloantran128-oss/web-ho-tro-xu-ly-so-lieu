"""Tạo dữ liệu khảo sát MÔ PHỎNG (không phải dữ liệu thật) để học sinh và giáo viên chạy thử.
Chạy: python tao_du_lieu_mau.py  →  khao-sat-mau.csv"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)
n = 200

gioi = rng.choice(["Nam", "Nữ"], n, p=[0.46, 0.54])
khoi = rng.choice([10, 11, 12], n, p=[0.35, 0.33, 0.32])

# Căng thẳng tiềm ẩn: khối 12 cao hơn một chút
stress = rng.normal(0, 1, n) + (khoi == 12) * 0.4


def likert(latent, lo, hi, reverse=False):
    raw = np.round((hi + lo) / 2 + latent * (hi - lo) / 4 + rng.normal(0, 0.6, len(latent)))
    raw = np.clip(raw, lo, hi).astype(int)
    return (lo + hi - raw) if reverse else raw


df = pd.DataFrame({"GioiTinh": gioi, "Khoi": khoi})
# PSS-10 (0–4): câu 4, 5, 7, 8 phát biểu tích cực nên trả lời ngược chiều căng thẳng
for i in range(1, 11):
    df[f"PSS{i}"] = likert(stress, 0, 4, reverse=i in (4, 5, 7, 8))

# Thang tự xây dựng "Hứng thú học tập" (1–5), TT4 là câu phát biểu ngược
trust = rng.normal(0, 1, n) + (gioi == "Nữ") * 0.3
for i in range(1, 5):
    df[f"TT{i}"] = likert(trust, 1, 5, reverse=(i == 4))

# Câu nhiều lựa chọn kiểu Google Forms: các lựa chọn nối bằng ", " trong một ô.
# "Bạn bè, người thân" có dấu phẩy bên trong; vài người tự ghi câu trả lời khác.
kenh = {"Facebook": 0.75, "TikTok": 0.65, "Website, báo điện tử": 0.35, "Bạn bè, người thân": 0.45, "YouTube": 0.25}
answers = []
for i in range(n):
    chosen = [k for k, p in kenh.items()
              if rng.random() < p + (0.12 if k == "TikTok" and gioi[i] == "Nữ" else 0)]
    if rng.random() < 0.03:
        chosen.append("Hội thảo, câu lạc bộ")
    answers.append(", ".join(chosen) if chosen else np.nan)
df["KenhThongTin"] = answers

# Vài ô trống để thấy cách xử lý dữ liệu thiếu
for col in ("PSS3", "TT2"):
    df.loc[rng.choice(n, 3, replace=False), col] = np.nan

out = Path(__file__).with_name("khao-sat-mau.csv")
df.to_csv(out, index=False, encoding="utf-8-sig")
print(f"Đã tạo {out} ({len(df)} dòng)")
