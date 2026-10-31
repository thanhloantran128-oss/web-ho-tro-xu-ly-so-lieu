---
ten: Bảng tần suất (Frequencies)
dung_cho: tan-suat
nguon: Nguyên tắc báo cáo dữ liệu thiếu và thận trọng với ô có ít quan sát phỏng theo open-scholar-skill/scholar-eda (Zhang, 2026) – Open Scholar Skill License (Academic Use). Phần còn lại biên soạn mới cho học sinh THPT.
---

# Mục đích

Đếm xem **mỗi lựa chọn có bao nhiêu người chọn** và chiếm bao nhiêu phần trăm. Dùng cho biến định danh (giới tính, nền tảng MXH), biến thứ bậc (khối lớp, mức thu nhập) và để xem phân bố từng mức của câu hỏi Likert.

# Cách đọc bảng tần suất (giống SPSS)

| Cột | Ý nghĩa | Khi nào dùng |
|---|---|---|
| **Frequency (Tần số)** | Số người chọn | Luôn báo cáo |
| **Percent (%)** | Tỷ lệ trên **tổng số phiếu**, kể cả người bỏ trống | Ít dùng khi có dữ liệu thiếu |
| **Valid Percent (% hợp lệ)** | Tỷ lệ trên **số người có trả lời** | **Nên dùng cột này để báo cáo** |
| **Cumulative Percent (% tích lũy)** | Cộng dồn % hợp lệ từ trên xuống | Chỉ có nghĩa với biến **thứ bậc** (ví dụ: "65% học sinh dùng MXH từ 3 giờ trở xuống") |

Nếu không có dữ liệu thiếu thì cột Percent và Valid Percent bằng nhau.

# Điều cần kiểm tra

- **Tổng % hợp lệ phải bằng 100%**. Có thể lệch 0,1 do làm tròn, và nên ghi chú điều này.
- **Nhóm quá nhỏ**: nhóm có dưới 5 người thì kết luận về nhóm đó rất kém tin cậy. Nếu sau này dùng biến này để so sánh nhóm (t-test, ANOVA), nên **gộp nhóm** (ví dụ gộp "Twitter", "Threads" thành "Khác").
- **Lựa chọn "Khác"** chiếm tỷ lệ lớn (trên 10%) thì nên đọc câu trả lời mở để tạo thêm nhóm mới.
- **Câu hỏi chọn nhiều đáp án** (ví dụ "Bạn dùng những MXH nào?"): tổng % sẽ lớn hơn 100%. Đây không phải lỗi. Phải ghi rõ "% trên số người trả lời, một người có thể chọn nhiều đáp án".

# Chọn biểu đồ

| Tình huống | Biểu đồ nên dùng |
|---|---|
| Biến định danh, ít nhóm (2–5) | Biểu đồ cột hoặc tròn |
| Biến định danh, nhiều nhóm | Biểu đồ cột ngang, sắp xếp từ cao xuống thấp |
| Biến thứ bậc | Biểu đồ cột **giữ đúng thứ tự** các mức |
| Câu hỏi Likert | Biểu đồ cột chồng 100% (các mức từ "Rất không đồng ý" đến "Rất đồng ý") |

Không dùng biểu đồ tròn khi có trên 5 nhóm hoặc khi là câu hỏi chọn nhiều đáp án.

# Dữ liệu đầu vào AI nhận

```json
{
  "analysis": "tan-suat",
  "variable": "NenTang",
  "label": "Nền tảng mạng xã hội sử dụng nhiều nhất",
  "type": "nominal | ordinal | likert",
  "multiple_response": false,
  "n_total": 200, "n_valid": 197, "n_missing": 3,
  "table": [
    {"value": 1, "label": "Facebook", "freq": 84, "percent": 42.0, "valid_percent": 42.6, "cum_percent": null},
    {"value": 2, "label": "TikTok", "freq": 71, "percent": 35.5, "valid_percent": 36.0, "cum_percent": null}
  ]
}
```

`cum_percent` để `null` với biến định danh.

# Lỗi học sinh hay mắc

- Báo cáo cột Percent khi có dữ liệu thiếu, làm % bị thấp hơn thực tế.
- Diễn giải % tích lũy cho biến định danh.
- Cộng % của câu chọn nhiều đáp án rồi lo lắng vì vượt 100%.
- Kết luận về toàn trường từ một nhóm chỉ có 3 người.
- Chỉ ghi % mà không ghi n. Nên ghi cả hai, ví dụ "42,6% (n = 84)".

# Mẫu câu viết báo cáo

> "Trong 197 học sinh trả lời, Facebook là nền tảng được sử dụng nhiều nhất (42,6%; n = 84), tiếp theo là TikTok (36,0%; n = 71). Ba học sinh không trả lời câu hỏi này."
