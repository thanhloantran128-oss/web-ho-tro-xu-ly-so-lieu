---
ten: Bảng chéo và kiểm định Chi-square (Crosstabs)
dung_cho: bang-cheo
nguon: Biên soạn mới cho học sinh THPT theo cách trình bày Crosstabs của SPSS. Nguyên tắc báo cáo độ lớn ảnh hưởng và không diễn giải nhân quả phỏng theo open-scholar-skill/scholar-analyze (Zhang, 2026) – Open Scholar Skill License (Academic Use).
---

# Mục đích

Xem hai biến **phân loại** có liên hệ với nhau không. Ví dụ: giới tính và nền tảng mạng xã hội dùng nhiều nhất; khối lớp và việc có đi học thêm.

# Loại thang đo phù hợp (ràng buộc bắt buộc)

| Dùng được | Không dùng được → thay bằng |
|---|---|
| Hai biến **định danh hoặc thứ bậc ít nhóm** | Biến số đo liên tục (điểm, số giờ) → chia nhóm trước, hoặc dùng **t-test/ANOVA** (nếu một biến là nhóm) hay **Tương quan** (nếu cả hai là số đo) |
| Mỗi người chỉ xuất hiện **một lần** trong bảng | Câu nhiều lựa chọn (một người ở nhiều ô) → dùng phép **Câu nhiều lựa chọn**, có phần so sánh nhóm |

# Điều kiện tần số kỳ vọng

- **Tần số kỳ vọng** (Expected Count) là số người lẽ ra có ở mỗi ô nếu hai biến không liên hệ.
- Chi-square cần **không quá 20% số ô có kỳ vọng < 5** và không ô nào < 1.
- **Bảng 2 × 2 có ô kỳ vọng < 5** thì đọc **Fisher's exact test**. Hệ thống tự chọn.
- Bảng lớn vi phạm điều kiện thì nên **gộp nhóm** rồi chạy lại.

# Cách đọc

1. Kiểm tra điều kiện tần số kỳ vọng.
2. Đọc χ²(df, *N*), *p*. Nếu *p* ≤ ,05 thì hai biến có liên hệ.
3. **Đọc % theo hàng** để biết liên hệ thế nào: so sánh tỷ lệ của cùng một nhóm cột giữa các hàng.
4. **Cramér's V** cho biết độ mạnh. Mốc của Cohen phụ thuộc bậc tự do *k* = min(số hàng, số cột) − 1:

| *k* | Nhỏ | Trung bình | Lớn |
|---|---|---|---|
| 1 (bảng 2 × …) | ,10 | ,30 | ,50 |
| 2 | ,07 | ,21 | ,35 |
| 3 | ,06 | ,17 | ,29 |

# Dữ liệu đầu vào AI nhận

```json
{"analysis": "bang-cheo", "hang": {"label": "Giới tính", "nhom": ["Nam", "Nữ"]},
 "cot": {"label": "Nền tảng chính", "nhom": ["Facebook", "TikTok"]}, "n": 196,
 "tan_so": [[50, 39], [41, 66]], "pct_hang": [[56.2, 43.8], [38.3, 61.7]], "ky_vong": [[...]],
 "chi2": 6.31, "df": 1, "p": 0.012, "cramers_v": 0.18, "pct_o_ky_vong_nho": 0, "fisher_p": null,
 "kiem_dinh_nen_doc": "chi2"}
```

# Lỗi học sinh hay mắc

- So sánh tần số tuyệt đối giữa các nhóm có cỡ khác nhau. Phải so sánh **%**.
- Đọc % theo cột khi câu hỏi nghiên cứu là "nhóm hàng khác nhau thế nào".
- Bỏ qua điều kiện tần số kỳ vọng khi có nhiều nhóm nhỏ.
- Kết luận nhân quả: "vì là nữ nên dùng TikTok".
- Đưa biến số đo (điểm thi) vào bảng chéo, tạo ra hàng chục cột.

# Mẫu câu viết báo cáo

> "Kết quả kiểm định Chi-square cho thấy có liên hệ có ý nghĩa thống kê giữa giới tính và nền tảng mạng xã hội dùng nhiều nhất, χ²(1, *N* = 196) = 6,31; *p* = ,012; Cramér's V = ,18. Cụ thể, tỷ lệ dùng TikTok ở nữ (61,7%) cao hơn nam (43,8%)."
