"""Xem tổng hợp đánh giá của người dùng và xuất toàn bộ ra file Excel-đọc-được (CSV).
Chạy (trong thư mục stats-api): .venv\\Scripts\\python xem_danh_gia.py"""
import csv
from pathlib import Path

from app import feedback

rows = feedback.load()
s = feedback.summary(rows, so_gop_y=20)
TEN = {"huu_ich": "Mức độ hữu ích", "chinh_xac": "Độ chính xác, tin cậy", "de_dung": "Dễ sử dụng"}

print(f"Tổng số lượt đánh giá: {s['so_luot']}\n")
for key, name in TEN.items():
    d = s["diem"][key]
    if not d["n"]:
        continue
    bars = "  ".join(f"{k}★:{v}" for k, v in d["phan_bo"].items())
    print(f"{name:<24} TB = {str(d['trung_binh']).replace('.', ',')}/5 · {str(d['ty_le_4_5']).replace('.', ',')}% chọn 4–5 · {bars}")
print("\nĐối chiếu với phần mềm khác:", ", ".join(f"{k}: {v}" for k, v in s["doi_chieu"].items()))
print("Vai trò:", ", ".join(f"{k}: {v}" for k, v in s["vai_tro"].items()))
print("Phép phân tích đã dùng trước khi đánh giá:", ", ".join(f"{k}: {v}" for k, v in s["phep_phan_tich"].items()))
print("\nGóp ý gần đây:")
for g in s["gop_y_gan_day"]:
    print(f"- [{g['thoi_gian']}] (hữu ích {g['huu_ich']}, chính xác {g['chinh_xac']}, dễ dùng {g['de_dung']}) {g['gop_y']}")

out = Path(__file__).with_name("danh-gia.csv")
cols = ["thoi_gian", "vai_tro", "phep_phan_tich", "huu_ich", "chinh_xac", "doi_chieu", "de_dung", "gop_y"]
with out.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
print(f"\nĐã xuất toàn bộ {len(rows)} lượt ra {out}")
