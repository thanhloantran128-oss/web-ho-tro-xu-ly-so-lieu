---
ten: Phân tích phương sai một yếu tố (One-way ANOVA)
dung_cho: anova
nguon: Nguyên tắc kiểm tra điều kiện, báo cáo độ lớn ảnh hưởng và không diễn giải nhân quả phỏng theo open-scholar-skill/scholar-analyze (Zhang, 2026) – Open Scholar Skill License (Academic Use). Phần hướng dẫn đọc bảng SPSS và kiểm định sau biên soạn mới cho học sinh THPT.
---

# Mục đích

So sánh **trung bình của từ 3 nhóm trở lên** trong một lần kiểm định. Ví dụ: mức nhận biết thương hiệu có khác nhau giữa khối 10, 11, 12 không? Giữa các nhóm thu nhập gia đình?

**Vì sao không làm nhiều t-test?** 3 nhóm cần 3 cặp so sánh, 5 nhóm cần 10 cặp. Mỗi lần kiểm định có 5% khả năng "báo động giả", làm nhiều lần thì khả năng ít nhất một lần báo động giả tăng mạnh (với 10 cặp là khoảng 40%). ANOVA kiểm soát được sai lầm này.

# Loại thang đo phù hợp (ràng buộc bắt buộc)

| Vai trò | Được dùng | Không được dùng → phép thay thế |
|---|---|---|
| **Biến phụ thuộc** | Thang **khoảng / tỷ lệ**, hoặc **điểm trung bình của thang Likert nhiều câu** | Biến định danh / nhị phân → Chi-square (so sánh tỷ lệ) |
| | ⚠ **Một câu Likert đơn lẻ / biến thứ bậc ít mức**: chỉ dùng như tham khảo | Ưu tiên điểm cả thang, hoặc đọc kết quả Kruskal-Wallis |
| **Biến nhóm (yếu tố)** | Biến **định danh hoặc thứ bậc** có **từ 3 nhóm** (khối lớp, mức thu nhập…) | 2 nhóm → Independent t-test. Biến số đo liên tục → chia nhóm hoặc dùng tương quan. Quá nhiều nhóm (> 10) → gộp nhóm |
| **Thiết kế** | Mỗi người thuộc **đúng một** nhóm | Cùng một người đo nhiều lần → ANOVA đo lặp / Friedman (ngoài phạm vi) |

Hệ thống web tự kiểm tra các ràng buộc này. Khi giải thích, AI phải nhắc lại cảnh báo trong `kiem_tra_dieu_kien` nếu có.

# Bước 1 – Kiểm tra điều kiện

1. **Biến phụ thuộc định lượng** (điểm, trung bình thang Likert).
2. **Biến độc lập là biến phân nhóm** có từ 3 nhóm trở lên, mỗi người chỉ thuộc **một** nhóm.
3. **Quan sát độc lập.**
4. **Phân phối xấp xỉ chuẩn trong mỗi nhóm.** ANOVA khá chịu đựng việc lệch chuẩn khi mỗi nhóm có khoảng 20–30 người trở lên.
5. **Phương sai đồng nhất giữa các nhóm**, kiểm tra bằng **Levene** (bảng *Test of Homogeneity of Variances*).
6. **Cỡ nhóm**: nhóm có dưới khoảng 10 người thì kết quả kém tin cậy, nên **gộp nhóm** trước. Ví dụ gộp các mức thu nhập ít người thành một nhóm. Cỡ nhóm chênh lệch quá nhiều (ví dụ 120 – 60 – 8) cũng làm kết quả kém ổn định.

# Bước 2 – Chọn hướng phân tích theo Levene

| Kết quả Levene | Kiểm định tổng thể | Kiểm định sau (post hoc) |
|---|---|---|
| Sig. **> 0,05** (phương sai đồng nhất) | Bảng **ANOVA** (F thường) | **Tukey HSD** |
| Sig. **≤ 0,05** (phương sai không đồng nhất) | Bảng **Robust Tests of Equality of Means → Welch** | **Games-Howell** |
| Phân phối lệch mạnh và nhóm nhỏ | **Kruskal-Wallis H** (phi tham số) | So sánh từng cặp có hiệu chỉnh (Dunn–Bonferroni) |

# Bước 3 – Đọc kết quả

## Bảng Descriptives
N, Mean, Std. Deviation từng nhóm. Dùng để biết **nhóm nào cao, nhóm nào thấp**.

## Bảng ANOVA (hoặc Welch)
- **F**: tỷ số giữa biến thiên **giữa các nhóm** và biến thiên **trong từng nhóm**. F càng lớn thì các nhóm càng tách biệt.
- **df**: hai bậc tự do (Between Groups và Within Groups). Welch có df2 là số lẻ.
- **Sig.**:
  - **≤ 0,05** → có **ít nhất một cặp nhóm** khác nhau. Lúc này **mới** đọc post hoc để biết cặp nào.
  - **> 0,05** → chưa đủ bằng chứng để kết luận các nhóm khác nhau. **Không** đi tìm cặp khác biệt trong post hoc.

Nhấn mạnh với học sinh: ANOVA có ý nghĩa **không cho biết** nhóm nào khác nhóm nào, chỉ biết "không phải tất cả đều bằng nhau".

## Bảng Multiple Comparisons (post hoc)
- Mỗi dòng là một cặp nhóm (I) – (J).
- **Mean Difference (I−J)**: dấu `*` nghĩa là cặp đó khác biệt có ý nghĩa ở mức 0,05.
- **Sig.** của từng cặp đã được hiệu chỉnh cho nhiều lần so sánh.
- Mỗi cặp xuất hiện 2 lần (A–B và B–A), chỉ cần đọc một lần.

# Bước 4 – Độ lớn ảnh hưởng (Eta bình phương, η²)

η² = SS Between / SS Total, cho biết **bao nhiêu % biến thiên** của biến phụ thuộc gắn với việc thuộc nhóm nào.

| η² | Mức ảnh hưởng (quy ước Cohen) |
|---|---|
| < 0,01 | Rất nhỏ |
| 0,01 – < 0,06 | Nhỏ |
| 0,06 – < 0,14 | Trung bình |
| ≥ 0,14 | Lớn |

SPSS từ bản 27 có bảng "ANOVA Effect Sizes". Nếu dữ liệu đầu vào không có η² thì nói rõ là chưa có, **không tự tính**.

# Dữ liệu đầu vào AI nhận

```json
{
  "analysis": "anova",
  "dv": {"name": "NB", "label": "Nhận biết thương hiệu (TB thang 1–5)"},
  "factor": {"name": "Khoi", "label": "Khối lớp"},
  "groups": [
    {"label": "Khối 10", "n": 70, "mean": 3.48, "sd": 0.70},
    {"label": "Khối 11", "n": 66, "mean": 3.66, "sd": 0.68},
    {"label": "Khối 12", "n": 64, "mean": 3.89, "sd": 0.61}
  ],
  "levene": {"F": 0.92, "df1": 2, "df2": 197, "p": 0.400},
  "anova": {"F": 6.35, "df1": 2, "df2": 197, "p": 0.002, "eta_sq": 0.061},
  "welch": {"F": 6.62, "df1": 2, "df2": 131.2, "p": 0.002},
  "posthoc": {
    "method": "Tukey HSD | Games-Howell",
    "pairs": [
      {"i": "Khối 10", "j": "Khối 11", "mean_diff": -0.18, "p": 0.272},
      {"i": "Khối 10", "j": "Khối 12", "mean_diff": -0.41, "p": 0.001},
      {"i": "Khối 11", "j": "Khối 12", "mean_diff": -0.23, "p": 0.112}
    ]
  },
  "nonparametric": {"test": "Kruskal-Wallis", "H": 12.05, "df": 2, "p": 0.002}
}
```

Máy tính thống kê tự chọn `posthoc.method` theo Levene (p > 0,05 → Tukey, ngược lại → Games-Howell). AI phải kiểm tra lại sự phù hợp này và nhắc nếu không khớp.

# Lỗi học sinh hay mắc

- Làm t-test cho từng cặp thay vì ANOVA.
- Đọc post hoc khi ANOVA tổng thể không có ý nghĩa, rồi "tìm ra" một cặp khác biệt.
- Dùng Tukey khi Levene có p ≤ 0,05 (phải dùng Games-Howell và đọc Welch).
- Giữ nguyên nhóm chỉ có 3–5 người.
- Viết "khối 12 nhận biết cao nhất" chỉ vì trung bình cao nhất, trong khi post hoc cho thấy chỉ khác khối 10.
- Dùng ANOVA một yếu tố khi cùng một người được đo nhiều lần (phải dùng ANOVA đo lặp hoặc Friedman, ngoài phạm vi skill này).

# Mẫu câu viết báo cáo

**Có ý nghĩa, phương sai đồng nhất:**
> "Kiểm định Levene cho thấy phương sai giữa các khối đồng nhất (p = 0,400). Kết quả One-way ANOVA cho thấy mức nhận biết thương hiệu khác nhau có ý nghĩa giữa các khối lớp, F(2, 197) = 6,35; p = 0,002; η² = 0,061 (mức ảnh hưởng trung bình). Kiểm định sau Tukey HSD cho thấy học sinh khối 12 (M = 3,89; ĐLC = 0,61) có mức nhận biết cao hơn khối 10 (M = 3,48; ĐLC = 0,70), p = 0,001; các cặp còn lại không khác biệt có ý nghĩa."

**Phương sai không đồng nhất:**
> "Do giả định phương sai đồng nhất bị vi phạm (Levene, p = 0,012), kiểm định Welch được sử dụng: F(2; 131,2) = 6,62; p = 0,002. Kiểm định sau Games-Howell cho thấy…"

**Không có ý nghĩa:**
> "Chưa tìm thấy khác biệt có ý nghĩa thống kê về mức nhận biết thương hiệu giữa các nhóm thu nhập, F(3, 196) = 1,08; p = 0,359."
