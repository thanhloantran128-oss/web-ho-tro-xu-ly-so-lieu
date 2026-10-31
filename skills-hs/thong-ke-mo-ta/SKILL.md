---
ten: Thống kê mô tả (tổng quan)
dung_cho: mo-ta
nguon: Các nguyên tắc về bảng mô tả mẫu (Table 1), báo cáo dữ liệu thiếu và kiểm tra phân phối phỏng theo open-scholar-skill/scholar-eda và scholar-analyze (Zhang, 2026) – Open Scholar Skill License (Academic Use). Đã rút gọn và biên soạn lại cho học sinh THPT.
---

# Mục đích

Thống kê mô tả trả lời câu hỏi **"mẫu khảo sát của bạn trông như thế nào?"**, trước khi kiểm định bất kỳ giả thuyết nào. Đây là bước bắt buộc: không mô tả mẫu thì người đọc không biết kết quả áp dụng cho ai.

# Bước 1 – Xác định loại biến (quan trọng nhất)

| Loại biến | Ví dụ | Chỉ số nên dùng | Không nên dùng |
|---|---|---|---|
| **Định danh** (nominal) – các nhóm không có thứ tự | Giới tính, lớp chuyên, nền tảng MXH chính | Tần số, % , mode (giá trị xuất hiện nhiều nhất) | Trung bình, độ lệch chuẩn |
| **Thứ bậc** (ordinal) – có thứ tự nhưng khoảng cách không đều | Khối lớp 10/11/12, mức thu nhập theo khoảng, xếp hạng | Tần số, %, % tích lũy, trung vị | Trung bình (trừ khi giải thích rõ) |
| **Khoảng / tỷ lệ** (scale) – số đo thật | Điểm thi, số giờ dùng MXH/ngày, tuổi | Trung bình, độ lệch chuẩn, min, max, trung vị | — |
| **Thang Likert** (1–5, 1–7) | "Tôi thấy tin tưởng trường X" | Trong nghiên cứu khoa học xã hội thường được xử lý như biến khoảng: trung bình, độ lệch chuẩn, **kèm** tần suất từng mức | — |

Khi học sinh tính "trung bình giới tính = 1,45", hãy giải thích nhẹ nhàng vì sao con số này vô nghĩa và đề nghị dùng tần suất.

Câu hỏi Likert riêng lẻ: nên báo cáo cả trung bình lẫn phân bố % từng mức. Biến tổng hợp (trung bình của nhiều câu trong cùng thang đo, sau khi đã kiểm định Cronbach): dùng trung bình và độ lệch chuẩn.

# Bước 2 – Kiểm tra dữ liệu trước khi mô tả

- **Dữ liệu thiếu**: báo cáo số người không trả lời mỗi câu. Nếu một biến thiếu trên 10% thì cần nêu rõ trong báo cáo và nghĩ xem vì sao thiếu.
- **Giá trị bất thường**: giá trị ngoài thang đo (ví dụ "6" trong thang 1–5, tuổi 150) là lỗi nhập liệu. Phải sửa hoặc loại trước khi tính.
- **Câu hỏi đảo chiều**: câu hỏi phát biểu ngược ("Tôi KHÔNG tin tưởng…") phải mã hóa lại (1↔5, 2↔4) trước khi tính trung bình thang đo.
- **Cỡ mẫu phân tích (N)**: luôn ghi N thực tế dùng trong phân tích, không phải số phiếu phát ra.

# Bước 3 – Xem hình dạng phân phối (với biến khoảng/Likert)

| Chỉ số | Ý nghĩa | Ngưỡng tham khảo |
|---|---|---|
| **Độ lệch (Skewness)** | Phân phối lệch về một phía. Dương: đuôi dài bên phải (đa số điểm thấp); âm: đuôi dài bên trái (đa số điểm cao) | \|Skewness\| < 1: gần cân đối; 1–2: lệch vừa; > 2: lệch mạnh |
| **Độ nhọn (Kurtosis)** (SPSS báo cáo độ nhọn "vượt mức", phân phối chuẩn = 0) | Phân phối nhọn hay bẹt so với phân phối chuẩn | \|Kurtosis\| < 2: chấp nhận được với nghiên cứu ở mức học sinh |
| **Histogram** | Hình ảnh trực quan | Xem có một đỉnh hay nhiều đỉnh, có giá trị lạc xa không |

Các ngưỡng trên là quy ước thực hành, có nhiều tài liệu dùng ngưỡng khác (ví dụ ±2 cho skewness). Hãy nói rõ với học sinh rằng đây là quy ước, không phải luật tuyệt đối.

Hệ quả: phân phối lệch mạnh thì nên báo cáo **trung vị** bên cạnh trung bình, và cân nhắc kiểm định phi tham số khi so sánh nhóm (xem skill t-test, ANOVA).

# Bước 4 – Bảng mô tả mẫu (bảng 1 trong báo cáo)

Mọi báo cáo nghiên cứu nên có một bảng mô tả đặc điểm mẫu, ví dụ:

| Đặc điểm | n | % |
|---|---|---|
| Giới tính – Nam | 92 | 46,0 |
| Giới tính – Nữ | 108 | 54,0 |
| Khối 10 | 70 | 35,0 |
| … | | |
| **Biến khoảng** | **Trung bình** | **Độ lệch chuẩn** |
| Thời gian dùng MXH (giờ/ngày) | 3,42 | 1,15 |

Ghi chú dưới bảng: N tổng, số dữ liệu thiếu (nếu có).

# Dữ liệu đầu vào AI nhận

```json
{
  "analysis": "mo-ta",
  "n_total": 200,
  "variables": [
    {
      "name": "TG_MXH",
      "label": "Thời gian dùng MXH (giờ/ngày)",
      "type": "scale | ordinal | nominal | likert",
      "n_valid": 198, "n_missing": 2,
      "mean": 3.42, "sd": 1.15, "median": 3.0, "min": 0.5, "max": 8.0,
      "skewness": 0.84, "kurtosis": 0.61
    }
  ]
}
```

Với biến định danh/thứ bậc, máy tính thống kê chuyển sang định dạng của skill `tan-suat`.

# Lỗi học sinh hay mắc

- Tính trung bình cho biến định danh (giới tính, nơi ở).
- Chỉ báo cáo trung bình mà quên độ lệch chuẩn.
- Báo cáo N phát ra thay vì N hợp lệ.
- Quên mã hóa ngược câu hỏi đảo chiều nên trung bình thang đo bị sai.
- Bỏ qua bước mô tả, nhảy thẳng vào kiểm định.

# Mẫu câu viết báo cáo

> "Mẫu nghiên cứu gồm 200 học sinh, trong đó nữ chiếm 54,0% (n = 108). Thời gian sử dụng mạng xã hội trung bình là 3,42 giờ/ngày (ĐLC = 1,15), dao động từ 0,5 đến 8 giờ. Phân phối hơi lệch phải (Skewness = 0,84) nhưng vẫn trong ngưỡng chấp nhận."
