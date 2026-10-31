---
ten: Phân tích tương quan (Pearson, Spearman)
dung_cho: tuong-quan
nguon: Biên soạn mới cho học sinh THPT. Mốc độ mạnh theo Cohen (1988). Nguyên tắc không diễn giải nhân quả phỏng theo open-scholar-skill/scholar-analyze (Zhang, 2026) – Open Scholar Skill License (Academic Use).
---

# Mục đích

Xem hai biến **định lượng** có thay đổi cùng nhau không: "càng… càng…" (thuận) hay "càng… càng ít…" (nghịch), và mức độ chặt chẽ. Ví dụ: số giờ dùng mạng xã hội và mức căng thẳng.

# Loại thang đo phù hợp (ràng buộc bắt buộc)

| Biến | Pearson (*r*) | Spearman (*r*ₛ) |
|---|---|---|
| Số đo, điểm trung bình thang nhiều câu, phân phối gần chuẩn | ✔ | ✔ |
| Một câu Likert đơn lẻ / biến thứ bậc ít mức | ⚠ không nên | ✔ |
| Phân phối lệch mạnh, có giá trị cực đoan | ⚠ không nên | ✔ |
| Biến nhị phân (0/1) | ⚠ dùng t-test sẽ dễ hiểu hơn | ⚠ |
| Biến định danh (giới tính, lớp) | ✘ → Bảng chéo / t-test / ANOVA | ✘ |

Hệ thống web chặn biến định danh và cảnh báo các trường hợp ⚠.

# Cách đọc

- **Dấu**: dương là thuận, âm là nghịch.
- **Độ lớn |r|**: dưới ,10 rất yếu; ,10–,29 yếu; ,30–,49 trung bình; từ ,50 trở lên mạnh (Cohen, 1988).
- **p**: tương quan có khác 0 trong tổng thể không. Mẫu lớn thì *r* rất nhỏ cũng có thể có *p* < ,05. Hãy luôn xem độ lớn.
- **Nhiều cặp cùng lúc**: xem *p* hiệu chỉnh Bonferroni.
- Báo cáo theo APA: *r*(df) với df = *n* − 2; *r* không có số 0 đầu (*r* = ,45).

# Dữ liệu đầu vào AI nhận

```json
{"analysis": "tuong-quan", "phuong_phap": "pearson",
 "bien": [{"name": "GioMXH", "label": "Giờ dùng MXH", "n": 198, "mean": 3.4, "sd": 1.2, "skewness": 0.8}],
 "cap": [{"x_label": "Giờ dùng MXH", "y_label": "Căng thẳng", "n": 195, "r": 0.31, "df": 193, "p": 0.00001,
          "ci95": [0.18, 0.43], "p_bonferroni": 0.00003}], "so_cap_kiem_dinh": 3}
```

# Lỗi học sinh hay mắc

- **Kết luận nhân quả**: "dùng mạng xã hội nhiều **gây** căng thẳng". Tương quan không chứng minh nhân quả.
- Chỉ nhìn *p*, bỏ qua độ lớn *r*.
- Dùng Pearson cho câu Likert đơn lẻ hoặc biến lệch mạnh.
- Tính tương quan với biến định danh được mã hóa số (1 = Nam, 2 = Nữ; 1 = 10A1, 2 = 10A2…).
- Không xét quan hệ không tuyến tính (tăng rồi giảm). *r* gần 0 chưa chắc là không có quan hệ.

# Mẫu câu viết báo cáo

> "Kết quả phân tích tương quan Pearson cho thấy thời gian sử dụng mạng xã hội và mức căng thẳng có tương quan thuận mức trung bình, *r*(193) = ,31; *p* < ,001."
