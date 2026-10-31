---
ten: Điểm trung bình và độ lệch chuẩn
dung_cho: trung-binh
nguon: Nguyên tắc luôn báo cáo trung bình kèm độ lệch chuẩn và N phỏng theo open-scholar-skill/scholar-analyze (Zhang, 2026) – Open Scholar Skill License (Academic Use). Phần diễn giải thang Likert biên soạn mới cho học sinh THPT.
---

# Mục đích

- **Trung bình (Mean, M)**: mức điểm "điển hình" của mẫu.
- **Độ lệch chuẩn (Std. Deviation, SD, ĐLC)**: các câu trả lời **phân tán** quanh trung bình nhiều hay ít.

Hai con số này luôn đi cùng nhau. Cùng trung bình 3,0 nhưng SD = 0,3 (mọi người nghĩ giống nhau) khác hoàn toàn SD = 1,5 (ý kiến rất chia rẽ).

# Cách đọc

| Chỉ số | Ý nghĩa | Lưu ý |
|---|---|---|
| **N** | Số người có trả lời | Báo cáo N hợp lệ |
| **Mean** | Tổng điểm chia cho N | Bị kéo mạnh bởi giá trị cực đoan |
| **Std. Deviation** | Khoảng cách "trung bình" từ mỗi câu trả lời đến Mean | Cùng đơn vị với biến |
| **Minimum / Maximum** | Giá trị nhỏ nhất / lớn nhất | Dùng để phát hiện lỗi nhập liệu (giá trị ngoài thang) |
| **Median (trung vị)** | Giá trị đứng giữa khi xếp từ thấp đến cao | Nên báo cáo thêm khi phân phối lệch mạnh |
| **Std. Error of Mean (SE)** | Độ chính xác của trung bình mẫu khi ước lượng trung bình tổng thể | **Không phải** độ lệch chuẩn, không được nhầm lẫn |

## Đánh giá độ lệch chuẩn với thang Likert 1–5

- SD < 0,6: ý kiến khá đồng nhất.
- SD khoảng 0,6–1,0: mức phân tán thường gặp.
- SD > 1,2: ý kiến chia rẽ. Nên xem bảng tần suất để biết có hai "phe" trái ngược không.

Đây là gợi ý để diễn giải, không phải ngưỡng chuẩn.

# Diễn giải trung bình thang Likert 5 mức

Quy ước phổ biến trong các nghiên cứu ở Việt Nam là chia khoảng đều với độ rộng = (5 − 1) / 5 = 0,8:

| Khoảng trung bình | Mức đánh giá |
|---|---|
| 1,00 – 1,80 | Rất không đồng ý / Rất thấp |
| 1,81 – 2,60 | Không đồng ý / Thấp |
| 2,61 – 3,40 | Trung lập / Trung bình |
| 3,41 – 4,20 | Đồng ý / Cao |
| 4,21 – 5,00 | Rất đồng ý / Rất cao |

Thang 7 mức: độ rộng = (7 − 1) / 7 ≈ 0,86, chia tương tự (bảng chi tiết trong `scales/likert-tu-xay-dung.yaml`).

**Chỉ dùng bảng này cho thang Likert TỰ XÂY DỰNG.** Thang chuẩn (DASS-21, PSS-10, SCS, RSES, SWLS…) có cách tính điểm và ngưỡng riêng. Khi dữ liệu đầu vào có mục `scale` với mã thang chuẩn, chuyển sang skill `cham-diem-thang-do`.

Nhắc học sinh rằng đây là **quy ước để diễn giải**, cần ghi rõ trong phần phương pháp. Không được coi là kiểm định thống kê. Muốn biết trung bình có thật sự cao hơn mức trung lập (3) hay không thì dùng **One-sample t-test** với giá trị kiểm định = 3.

# So sánh trung bình giữa các nhóm hay các biến

- Trung bình nhóm A cao hơn nhóm B **chưa có nghĩa** là khác biệt có ý nghĩa thống kê. Phải dùng t-test (2 nhóm) hoặc ANOVA (từ 3 nhóm).
- Khi xếp hạng nhiều câu hỏi theo trung bình, chỉ nên nói "cao nhất / thấp nhất trong mẫu", không khẳng định khác biệt nếu chưa kiểm định.

# Dữ liệu đầu vào AI nhận

```json
{
  "analysis": "trung-binh",
  "scale_points": 5,
  "variables": [
    {"name": "TT1", "label": "Tôi thấy hứng thú với các môn học",
     "n": 200, "mean": 3.86, "sd": 0.82, "median": 4, "min": 1, "max": 5, "se": 0.058,
     "skewness": -0.71}
  ],
  "composite": {"name": "TT", "label": "Hứng thú học tập (trung bình TT1–TT4)", "n": 200, "mean": 3.74, "sd": 0.69}
}
```

`scale_points` để `null` nếu không phải thang Likert.

# Lỗi học sinh hay mắc

- Báo cáo SE thay cho SD (SE nhỏ hơn rất nhiều nên trông "đẹp" hơn).
- Báo cáo trung bình không kèm SD.
- Viết "trung bình 3,86 tức là 86% đồng ý". Trung bình không phải tỷ lệ phần trăm.
- Kết luận nhóm A khác nhóm B chỉ vì trung bình chênh nhau, chưa kiểm định.
- Có giá trị Max = 55 trong thang 1–5 (lỗi nhập liệu) mà không phát hiện.

# Mẫu câu viết báo cáo

> "Hứng thú học tập của học sinh ở mức cao (M = 3,86; ĐLC = 0,82), cho thấy phần lớn học sinh đồng ý với nhận định này và mức độ phân tán ý kiến ở mức vừa phải."
