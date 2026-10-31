---
ten: Câu hỏi nhiều lựa chọn (Multiple Response)
dung_cho: nhieu-lua-chon
nguon: Biên soạn mới cho học sinh THPT, theo cách xử lý "Multiple Response Sets" của SPSS. Nguyên tắc báo cáo dữ liệu thiếu và thận trọng với nhóm nhỏ phỏng theo open-scholar-skill/scholar-eda (Zhang, 2026) – Open Scholar Skill License (Academic Use).
---

# Mục đích

Xử lý câu hỏi cho phép **chọn nhiều đáp án**, ví dụ "Bạn dùng những mạng xã hội nào?" hoặc "Bạn tìm thông tin học tập qua những kênh nào?". Mỗi người có thể chọn 0, 1 hoặc nhiều lựa chọn, nên **không** xử lý như bảng tần suất thông thường.

# Bước 1 – Nhận dạng cách dữ liệu được lưu

| Dạng | Ví dụ | Thường gặp khi |
|---|---|---|
| **Văn bản gộp** | Một cột chứa "Facebook, TikTok, Zalo" | Xuất từ Google Forms, Microsoft Forms |
| **Nhị phân (0/1)** | Mỗi lựa chọn là một cột; 1 = có chọn, 0 hoặc trống = không chọn | Nhập liệu SPSS, Excel tự thiết kế |

Với dạng văn bản gộp:
- Nên khai báo **danh sách lựa chọn gốc** của phiếu. Nhờ vậy hệ thống tách đúng cả những lựa chọn có dấu phẩy bên trong (ví dụ "Bạn bè, người thân").
- Phần chữ còn lại không khớp với lựa chọn nào được gom vào **"Khác"** (người trả lời tự ghi).

# Bước 2 – Hai loại phần trăm (điểm dễ nhầm nhất)

| Chỉ số | Cách tính | Trả lời câu hỏi | Tổng |
|---|---|---|---|
| **% số người** (Percent of Cases) | Số người chọn ÷ số người trả lời câu này | "Bao nhiêu % học sinh dùng TikTok?" | **Có thể > 100%** |
| **% lượt chọn** (Percent of Responses) | Số lượt chọn ÷ tổng số lượt chọn | "TikTok chiếm bao nhiêu % trong tất cả các lượt chọn?" | = 100% |

- **Mặc định báo cáo % số người**, vì đó là con số người đọc quan tâm.
- Tổng % số người vượt 100% **không phải lỗi**. Phải ghi chú: "một người có thể chọn nhiều đáp án".
- **Mẫu số là số người có trả lời câu hỏi**, không phải tổng số phiếu. Người bỏ trống cả câu được báo cáo riêng.
- **Số lựa chọn trung bình** mỗi người = tổng lượt chọn ÷ số người trả lời.

# Bước 3 – So sánh giữa các nhóm (tùy chọn)

Ví dụ: tỷ lệ dùng TikTok ở nam và nữ có khác nhau không?

- Mỗi lựa chọn được kiểm định riêng bằng **Chi-square (χ²)**: bảng "chọn / không chọn" × các nhóm.
- Bảng 2 × 2 có ô kỳ vọng < 5 thì dùng **Fisher's exact test**.
- Bảng lớn hơn mà có trên 20% ô kỳ vọng < 5 thì kết quả kém tin cậy; nên gộp nhóm.
- **Độ lớn ảnh hưởng: Cramér's V** (bảng 2 × 2 là φ). Mốc tham khảo: 0,10 nhỏ; 0,30 trung bình; 0,50 lớn.
- **Kiểm định nhiều lần:** có bao nhiêu lựa chọn thì làm bấy nhiêu lần kiểm định, nên khả năng "báo động giả" tăng. Hệ thống báo thêm **p hiệu chỉnh Bonferroni** (p × số lựa chọn, tối đa 1). Kết luận chắc chắn nên dựa trên p hiệu chỉnh.

Không dùng t-test hay ANOVA cho câu nhiều lựa chọn.

# Dữ liệu đầu vào AI nhận

```json
{
  "analysis": "nhieu-lua-chon",
  "label": "Mạng xã hội đang sử dụng",
  "dang": "van_ban | nhi_phan",
  "n_total": 200, "n_tra_loi": 196, "n_khong_tra_loi": 4,
  "tong_luot_chon": 431, "so_lua_chon_tb": 2.2,
  "table": [
    {"label": "Facebook", "freq": 150, "pct_nguoi": 76.5, "pct_luot": 34.8},
    {"label": "Khác", "freq": 6, "pct_nguoi": 3.1, "pct_luot": 1.4, "la_khac": true}
  ],
  "nhom_nho_duoi_5": [],
  "so_cau_tra_loi_khac": 6,
  "so_sanh_nhom": {
    "nhom": "Giới tính", "cac_nhom": [{"label": "Nam", "n": 89}, {"label": "Nữ", "n": 107}],
    "theo_lua_chon": [
      {"label": "TikTok", "pct_theo_nhom": [62.9, 78.5], "kiem_dinh": "Chi-square",
       "chi2": 5.73, "df": 1, "p": 0.017, "p_bonferroni": 0.083, "cramers_v": 0.17, "o_ky_vong_nho": false}
    ]
  }
}
```

# Lỗi học sinh hay mắc

- Cộng % số người rồi lo vì vượt 100%.
- Lấy tổng số phiếu làm mẫu số dù có người bỏ trống cả câu.
- Báo cáo % lượt chọn nhưng diễn giải như % số người ("34,8% học sinh dùng Facebook" là sai nếu 34,8% là % lượt chọn).
- Đếm thủ công trên Google Sheets khiến "Bạn bè, người thân" bị tách thành hai lựa chọn.
- Kiểm định 8 lựa chọn, thấy một lựa chọn có p = 0,04 rồi kết luận ngay mà không xét kiểm định nhiều lần.
- Dùng biểu đồ tròn cho câu nhiều lựa chọn. Nên dùng **biểu đồ cột ngang** sắp xếp từ cao xuống thấp.

# Mẫu câu viết báo cáo

> "Trong 196 học sinh trả lời, Facebook là mạng xã hội được sử dụng phổ biến nhất (76,5%), tiếp theo là TikTok (71,4%) và Zalo (52,0%). Trung bình mỗi học sinh sử dụng 2,2 nền tảng. Tỷ lệ được tính trên số người trả lời; một người có thể chọn nhiều đáp án nên tổng vượt 100%."

> "Tỷ lệ sử dụng TikTok ở nữ (78,5%) cao hơn ở nam (62,9%), χ²(1) = 5,73; *p* = ,017; φ = ,17. Tuy nhiên, sau khi hiệu chỉnh Bonferroni cho 5 lần so sánh, khác biệt không còn ý nghĩa thống kê (*p* = ,083)."
