# Ví dụ lời giải thích tự động

Sinh tự động từ dữ liệu MÔ PHỎNG `sample-data/khao-sat-mau.csv`. Sửa lời văn trong các file `.yaml` cùng thư mục rồi chạy lại `stats-api/tao_vi_du_giai_thich.py` để xem kết quả.

## Thống kê mô tả

### Lớp 1 – Tóm tắt

- Mẫu gồm 200 người; đã mô tả 2 biến.
- **Giới tính**: nhóm đông nhất là Nữ (55,5%; *n* = 111).
- **Câu PSS3**: *M* = 2,06; *SD* = 1,19; *Mdn* = 2; dao động từ 0 đến 4.

### Lớp 2 – Chi tiết

**Phép phân tích này để làm gì**

- Thống kê mô tả cho biết mẫu khảo sát của bạn trông như thế nào, trước khi kiểm định bất kỳ giả thuyết nào.

**Đọc kết quả**

- **Giới tính**: nhóm đông nhất là Nữ (55,5%; *n* = 111).
- **Câu PSS3**: *M* = 2,06; *SD* = 1,19; *Mdn* = 2; dao động từ 0 đến 4.

**Hình dạng phân phối**

- Phân phối của Câu PSS3 gần cân đối (skewness = −0,10).

**Mẫu câu báo cáo (APA)**

> Mẫu nghiên cứu gồm 200 người. Về Giới tính, nhóm Nữ chiếm tỷ lệ cao nhất (55,5%; *n* = 111). Câu PSS3 có trung bình 2,06 (*SD* = 1,19), dao động từ 0 đến 4.

**Câu hỏi gợi mở**

- Mẫu của bạn có đại diện được cho nhóm đối tượng bạn muốn kết luận không?
- Có biến nào phân bố bất thường mà bạn cần kiểm tra lại cách nhập liệu?

**Thuật ngữ**

- *M* (Mean) – trung bình
- *SD* (Standard Deviation) – độ lệch chuẩn: các câu trả lời phân tán quanh trung bình nhiều hay ít
- *Mdn* (Median) – trung vị: giá trị đứng giữa khi xếp từ thấp đến cao
- Skewness – độ lệch: phân phối lệch về một phía (dương: đuôi dài bên phải; âm: đuôi dài bên trái)
- Kurtosis – độ nhọn so với phân phối chuẩn
- Valid Percent – % hợp lệ: tỷ lệ trên số người có trả lời

## Tần suất – khối lớp

### Lớp 1 – Tóm tắt

- Nhóm **11** chiếm tỷ lệ cao nhất (36,0%; *n* = 72), tiếp theo là nhóm **12** (33,5%; *n* = 67), trong 200 người trả lời.

### Lớp 2 – Chi tiết

**Phép phân tích này để làm gì**

- Bảng tần suất đếm xem mỗi lựa chọn có bao nhiêu người chọn và chiếm bao nhiêu phần trăm.

**Đọc kết quả**

- Không có dữ liệu thiếu nên cột Percent và Valid Percent bằng nhau.
- Đây là biến có thứ tự nên cột Cumulative Percent có ý nghĩa (ví dụ: bao nhiêu % ở mức này trở xuống).
- Nhóm **11** chiếm tỷ lệ cao nhất (36,0%; *n* = 72), tiếp theo là nhóm **12** (33,5%; *n* = 67), trong 200 người trả lời.

**Mẫu câu báo cáo (APA)**

> Trong 200 người trả lời, nhóm 11 chiếm tỷ lệ cao nhất (36,0%; *n* = 72), tiếp theo là nhóm 12 (33,5%; *n* = 67).

**Câu hỏi gợi mở**

- Tỷ lệ này có khớp với những gì bạn dự đoán trước khi khảo sát không?
- Có nhóm nào quá nhỏ cần gộp lại trước khi phân tích tiếp không?

**Thuật ngữ**

- Valid Percent – % hợp lệ: tỷ lệ trên số người có trả lời
- Cumulative Percent – % tích lũy: cộng dồn từ trên xuống, chỉ có nghĩa với biến có thứ tự

## Trung bình – độ lệch chuẩn

### Lớp 1 – Tóm tắt

- **TT1**: *M* = 3,09; *SD* = 1,11 (*n* = 200).
- Theo quy ước chia khoảng đều của thang 5 mức, trung bình 3,09 thuộc mức **Trung bình / Trung lập**. Đây là quy ước để diễn giải, không phải kiểm định thống kê.
- **TT3**: *M* = 3,18; *SD* = 1,09 (*n* = 200).
- Theo quy ước chia khoảng đều của thang 5 mức, trung bình 3,18 thuộc mức **Trung bình / Trung lập**. Đây là quy ước để diễn giải, không phải kiểm định thống kê.

### Lớp 2 – Chi tiết

**Phép phân tích này để làm gì**

- Trung bình (*M*) cho biết mức điểm điển hình; độ lệch chuẩn (*SD*) cho biết ý kiến phân tán nhiều hay ít quanh trung bình. Hai con số này luôn đi cùng nhau.

**Đọc kết quả**

- **TT1**: *M* = 3,09; *SD* = 1,11 (*n* = 200).
- Theo quy ước chia khoảng đều của thang 5 mức, trung bình 3,09 thuộc mức **Trung bình / Trung lập**. Đây là quy ước để diễn giải, không phải kiểm định thống kê.
- **TT3**: *M* = 3,18; *SD* = 1,09 (*n* = 200).
- Theo quy ước chia khoảng đều của thang 5 mức, trung bình 3,18 thuộc mức **Trung bình / Trung lập**. Đây là quy ước để diễn giải, không phải kiểm định thống kê.
- Biến tổng hợp **Hứng thú học tập** (trung bình các câu): *M* = 3,09; *SD* = 0,96 (*n* = 197; 3 người bị loại vì thiếu câu trả lời).
- Theo quy ước chia khoảng đều của thang 5 mức, trung bình 3,09 thuộc mức **Trung bình / Trung lập**. Đây là quy ước để diễn giải, không phải kiểm định thống kê.

**Hình dạng phân phối**

- **TT1**: *SD* = 1,11: mức phân tán thường gặp.
- **TT3**: *SD* = 1,09: mức phân tán thường gặp.
- **Hứng thú học tập**: *SD* = 0,96: mức phân tán thường gặp.

**Lưu ý**

- Trung bình khác nhau giữa các câu hỏi hay các nhóm chưa có nghĩa là khác biệt có ý nghĩa thống kê. Muốn kết luận, hãy dùng t-test (2 nhóm) hoặc ANOVA (từ 3 nhóm).
- Muốn biết trung bình có thật sự cao hơn mức trung lập không, hãy dùng One-sample t-test với giá trị kiểm định là điểm giữa thang.

**Mẫu câu báo cáo (APA)**

> TT1 ở mức trung bình / trung lập (*M* = 3,09; *SD* = 1,11). TT3 ở mức trung bình / trung lập (*M* = 3,18; *SD* = 1,09). Hứng thú học tập ở mức trung bình / trung lập (*M* = 3,09; *SD* = 0,96).

**Câu hỏi gợi mở**

- Câu hỏi nào có trung bình cao nhất, thấp nhất? Điều đó gợi ý gì cho đề tài của bạn?
- Câu hỏi nào có ý kiến chia rẽ nhất (*SD* lớn nhất)? Vì sao?

**Thuật ngữ**

- *M* (Mean) – trung bình
- *SD* (Standard Deviation) – độ lệch chuẩn: các câu trả lời phân tán quanh trung bình nhiều hay ít
- *Mdn* (Median) – trung vị: giá trị đứng giữa khi xếp từ thấp đến cao

## Chấm điểm thang đo PSS-10 và Hứng thú học tập

### Lớp 1 – Tóm tắt

- **PSS-10 – điểm tổng**: *M* = 21,09; *SD* = 10,13 (*n* = 197).
- **Hứng thú học tập**: *M* = 3,11; *SD* = 0,95 (*n* = 197).

### Lớp 2 – Chi tiết

**Thang đo căng thẳng cảm nhận – 10 câu**

- Tính điểm thang đo căng thẳng cảm nhận – 10 câu theo đúng quy tắc của tác giả (đảo câu, cộng tổng hoặc lấy trung bình, nhân hệ số nếu có).
- **PSS-10 – điểm tổng**: *M* = 21,09; *SD* = 10,13 (*n* = 197).
- 3 người bị loại khỏi điểm PSS-10 – điểm tổng vì thiếu ít nhất một câu.
- Cronbach's α của PSS-10 – điểm tổng = ,96: rất tốt.
- Phân bố theo ngưỡng tham khảo: Thấp: 26,4%; Trung bình: 42,6%; Cao: 31,0%.
- Ngưỡng là quy ước thường dùng, không phải chuẩn chính thức (Quy ước phổ biến trong các tài liệu hướng dẫn thứ cấp. Tác giả gốc KHÔNG đưa ra điểm cắt mà khuyên so sánh với chuẩn của mẫu).
- Đây là thang đo về sức khỏe tinh thần: chỉ trình bày kết quả theo nhóm, không gắn nhãn cho cá nhân (ví dụ viết “x% có điểm ở mức vừa trở lên”, không viết “x% bị trầm cảm”).

**Thang Likert tự xây dựng**

- Mỗi biến được tính bằng trung bình các câu thuộc biến đó, sau khi đảo các câu phát biểu ngược.
- **Hứng thú học tập**: *M* = 3,11; *SD* = 0,95 (*n* = 197).
- 3 người bị loại khỏi điểm Hứng thú học tập vì thiếu ít nhất một câu.
- Cronbach's α của Hứng thú học tập = ,88: tốt.
- Phân bố theo ngưỡng tham khảo: Rất thấp / Rất không đồng ý: 12,2%; Thấp / Không đồng ý: 21,3%; Trung bình / Trung lập: 23,9%; Cao / Đồng ý: 27,4%; Rất cao / Rất đồng ý: 15,2%.
- Ngưỡng là quy ước thường dùng, không phải chuẩn chính thức (Quy ước chia khoảng đều thường dùng trong nghiên cứu ở Việt Nam; không phải chuẩn quốc tế).

**Lưu ý**

- Quên đảo 4 câu phát biểu tích cực (4, 5, 7, 8) sẽ làm điểm sai và Cronbach giảm mạnh.
- Không phải công cụ chẩn đoán.

**Mẫu câu báo cáo (APA)**

> PSS-10 – điểm tổng được đo bằng thang đo căng thẳng cảm nhận – 10 câu (Cohen, Kamarck & Mermelstein (1983); bản 10 câu: Cohen & Williamson (1988)). Độ tin cậy trong mẫu nghiên cứu: Cronbach's α = ,96. PSS-10 – điểm tổng có trung bình 21,09 (*SD* = 10,13). Hứng thú học tập có trung bình 3,11 (*SD* = 0,95). Cronbach's α = ,88.

**Câu hỏi gợi mở**

- Độ tin cậy trong mẫu của bạn có tương đương với nghiên cứu gốc không?
- Bạn sẽ dùng điểm thang đo này để so sánh giữa những nhóm nào?

**Thuật ngữ**

- *M* (Mean) – trung bình
- *SD* (Standard Deviation) – độ lệch chuẩn: các câu trả lời phân tán quanh trung bình nhiều hay ít
- Cronbach's α – độ nhất quán nội tại: các câu trong thang có cùng đo một khái niệm không
- Corrected Item-Total Correlation – tương quan biến–tổng hiệu chỉnh

## Independent t-test – Hứng thú học tập theo giới tính

### Lớp 1 – Tóm tắt

- **Nữ** (*M* = 3,28) có hứng thú học tập cao hơn **Nam** (*M* = 2,89); khác biệt có ý nghĩa thống kê (*p* = ,004).
- *d* = 0,42: mức ảnh hưởng nhỏ.

### Lớp 2 – Chi tiết

**Phép phân tích này để làm gì**

- Independent-samples t-test so sánh trung bình hứng thú học tập giữa hai nhóm người khác nhau (Nam và Nữ) để xem khác biệt là thật hay chỉ do ngẫu nhiên khi chọn mẫu.

**Kiểm tra điều kiện**

- Levene's test có *p* = ,065 > ,05: phương sai hai nhóm coi như bằng nhau. Bạn đọc dòng **Equal variances assumed** (Student).
- Phân phối không lệch mạnh, hoặc cỡ mẫu đủ lớn (mỗi nhóm từ 30 người trở lên) nên t-test vẫn phù hợp.

**Đọc kết quả**

- Trên dòng Student: *t*(195) = −2,90; *p* = ,004. Chênh lệch trung bình = −0,39, 95% CI [−0,65; −0,12].

**Mức ảnh hưởng**

- *d* = 0,42: mức ảnh hưởng nhỏ.

**Kết luận**

- **Nữ** (*M* = 3,28) có hứng thú học tập cao hơn **Nam** (*M* = 2,89); khác biệt có ý nghĩa thống kê (*p* = ,004).

**Lưu ý**

- Dữ liệu khảo sát chỉ cho thấy có khác biệt, không chứng minh được nguyên nhân.

**Mẫu câu báo cáo (APA)**

> Kết quả kiểm định Independent-samples t-test cho thấy Nữ (*M* = 3,28; *SD* = 0,88) có hứng thú học tập cao hơn Nam (*M* = 2,89; *SD* = 1,00), khác biệt có ý nghĩa thống kê, *t*(195) = −2,90; *p* = ,004; *d* = 0,42.

**Câu hỏi gợi mở**

- Theo bạn, điều gì có thể giải thích khác biệt này?
- Kết quả này ủng hộ hay bác bỏ giả thuyết ban đầu của bạn?
- Mức ảnh hưởng *d* = 0,42 có đủ lớn để tạo ra thay đổi trong thực tế không?

**Thuật ngữ**

- *M* (Mean) – trung bình
- *SD* (Standard Deviation) – độ lệch chuẩn: các câu trả lời phân tán quanh trung bình nhiều hay ít
- *t* – trị số kiểm định t: chênh lệch trung bình so với sai số
- *df* (degrees of freedom) – bậc tự do
- *p* (p-value) – mức ý nghĩa: xác suất thấy khác biệt lớn như vậy nếu thật ra không có khác biệt
- 95% CI (Confidence Interval) – khoảng tin cậy 95% của chênh lệch; không chứa 0 thì tương ứng *p* < ,05
- Levene's test – kiểm định phương sai đồng nhất giữa các nhóm
- Welch – cách tính hiệu chỉnh khi phương sai các nhóm khác nhau
- *d* (Cohen's d) – độ lớn khác biệt tính theo đơn vị độ lệch chuẩn
- Kiểm định phi tham số – không đòi hỏi phân phối chuẩn (Mann-Whitney U, Wilcoxon, Kruskal-Wallis)

## One-sample t-test – Hứng thú học tập so với mức trung lập 3

### Lớp 1 – Tóm tắt

- Chưa đủ bằng chứng để kết luận trung bình hứng thú học tập (*M* = 3,11) khác giá trị 3 (*p* = ,117).
- *d* = 0,11: khác biệt rất nhỏ, gần như không đáng kể trong thực tế.

### Lớp 2 – Chi tiết

**Phép phân tích này để làm gì**

- One-sample t-test so sánh trung bình hứng thú học tập của mẫu với giá trị 3 để xem mẫu có thật sự cao hơn hay thấp hơn giá trị này không.

**Kiểm tra điều kiện**

- Phân phối không lệch mạnh, hoặc cỡ mẫu đủ lớn (mỗi nhóm từ 30 người trở lên) nên t-test vẫn phù hợp.

**Đọc kết quả**

- Trên dòng Student: *t*(196) = 1,57; *p* = ,117. Chênh lệch trung bình = 0,11, 95% CI [−0,03; 0,24].

**Mức ảnh hưởng**

- *d* = 0,11: khác biệt rất nhỏ, gần như không đáng kể trong thực tế.

**Kết luận**

- Chưa đủ bằng chứng để kết luận trung bình hứng thú học tập (*M* = 3,11) khác giá trị 3 (*p* = ,117).

**Mẫu câu báo cáo (APA)**

> Trung bình hứng thú học tập (*M* = 3,11; *SD* = 0,95) không khác biệt có ý nghĩa thống kê so với giá trị 3, *t*(196) = 1,57; *p* = ,117.

**Câu hỏi gợi mở**

- Cỡ mẫu hiện tại có đủ lớn để phát hiện một khác biệt nhỏ không?
- Nếu khác biệt thật sự không tồn tại, điều đó nói gì về giả thuyết của bạn?

**Thuật ngữ**

- *M* (Mean) – trung bình
- *SD* (Standard Deviation) – độ lệch chuẩn: các câu trả lời phân tán quanh trung bình nhiều hay ít
- *t* – trị số kiểm định t: chênh lệch trung bình so với sai số
- *df* (degrees of freedom) – bậc tự do
- *p* (p-value) – mức ý nghĩa: xác suất thấy khác biệt lớn như vậy nếu thật ra không có khác biệt
- 95% CI (Confidence Interval) – khoảng tin cậy 95% của chênh lệch; không chứa 0 thì tương ứng *p* < ,05
- *d* (Cohen's d) – độ lớn khác biệt tính theo đơn vị độ lệch chuẩn
- Kiểm định phi tham số – không đòi hỏi phân phối chuẩn (Mann-Whitney U, Wilcoxon, Kruskal-Wallis)

## Câu nhiều lựa chọn – Kênh tìm thông tin học tập, so sánh theo giới tính

### Lớp 1 – Tóm tắt

- **Facebook** được chọn nhiều nhất (77,9% số người trả lời), tiếp theo là **TikTok** (69,7%) và **Website, báo điện tử** (39,5%).
- Trung bình mỗi người chọn 2,5 lựa chọn.

### Lớp 2 – Chi tiết

**Phép phân tích này để làm gì**

- Câu hỏi này cho phép chọn nhiều đáp án, nên mỗi người có thể được đếm ở nhiều lựa chọn. Bạn cần phân biệt % số người và % lượt chọn.

**Đọc kết quả**

- **% số người** (Percent of Cases) = số người chọn ÷ 195 người trả lời; tổng có thể vượt 100%. **% lượt chọn** (Percent of Responses) = số lượt chọn ÷ 483 lượt; tổng bằng 100%. Khi báo cáo, bạn dùng **% số người**.
- Trung bình mỗi người chọn 2,5 lựa chọn.
- Có 5 người bỏ trống cả câu; họ không được tính vào mẫu số.
- 5 người tự ghi câu trả lời khác ngoài danh sách; các câu này được gom vào nhóm **Khác**. Bạn nên đọc lại để xem có cần tạo thêm lựa chọn mới không.
- **Facebook** được chọn nhiều nhất (77,9% số người trả lời), tiếp theo là **TikTok** (69,7%) và **Website, báo điện tử** (39,5%).

**So sánh theo giới tính**

- Mỗi lựa chọn được kiểm định riêng bằng Chi-square (hoặc Fisher's exact khi bảng 2 × 2 có ô kỳ vọng < 5) để xem tỷ lệ chọn có khác nhau giữa các nhóm giới tính không.
- Có 5 lần kiểm định nên khả năng báo động giả tăng. Kết luận chắc chắn nên dựa trên *p* hiệu chỉnh Bonferroni.
- **TikTok**: tỷ lệ chọn khác nhau giữa các nhóm (Nam: 59,3%; Nữ: 78,0%); Chi-square, *p* = ,005, sau hiệu chỉnh *p* = ,024; Cramér's V = ,20.
- **Bạn bè, người thân**: tỷ lệ chọn khác nhau giữa các nhóm (Nam: 48,8%; Nữ: 27,5%); Chi-square, *p* = ,002, sau hiệu chỉnh *p* = ,011; Cramér's V = ,22.
- Các lựa chọn còn lại không khác biệt có ý nghĩa giữa các nhóm.

**Lưu ý**

- Không viết “x% học sinh chọn …” bằng con số % lượt chọn.
- Nên vẽ biểu đồ cột ngang theo % số người, sắp xếp từ cao xuống thấp; không dùng biểu đồ tròn.

**Mẫu câu báo cáo (APA)**

> Trong 195 người trả lời, Facebook là lựa chọn phổ biến nhất (77,9%), tiếp theo là TikTok (69,7%) và Website, báo điện tử (39,5%). Trung bình mỗi người chọn 2,5 lựa chọn. Tỷ lệ được tính trên số người trả lời; một người có thể chọn nhiều đáp án nên tổng vượt 100%. Tỷ lệ chọn TikTok khác nhau giữa các nhóm giới tính (Nam: 59,3%; Nữ: 78,0%), χ²(1) = 7,95; *p* = ,005 (hiệu chỉnh Bonferroni: *p* = ,024); Cramér's V = ,20. Tỷ lệ chọn Bạn bè, người thân khác nhau giữa các nhóm giới tính (Nam: 48,8%; Nữ: 27,5%), χ²(1) = 9,38; *p* = ,002 (hiệu chỉnh Bonferroni: *p* = ,011); Cramér's V = ,22.

**Câu hỏi gợi mở**

- Lựa chọn phổ biến nhất có khớp với dự đoán ban đầu của bạn không?
- Kết quả này gợi ý kênh nào nên được ưu tiên trong đề tài của bạn?

**Thuật ngữ**

- Percent of Cases – % số người: số người chọn ÷ số người trả lời; tổng có thể vượt 100%
- Percent of Responses – % lượt chọn: số lượt chọn ÷ tổng lượt chọn; tổng bằng 100%
- χ² (Chi-square) – kiểm định khác biệt về tỷ lệ giữa các nhóm
- Fisher's exact test – thay cho Chi-square khi bảng 2 × 2 có ô kỳ vọng nhỏ hơn 5
- Cramér's V (φ với bảng 2 × 2) – độ mạnh liên hệ; ,10 nhỏ; ,30 trung bình; ,50 lớn
- Hiệu chỉnh Bonferroni – nhân p với số lần kiểm định để tránh báo động giả khi kiểm định nhiều lần
- *p* (p-value) – mức ý nghĩa: xác suất thấy khác biệt lớn như vậy nếu thật ra không có khác biệt

## ANOVA – Căng thẳng theo khối

### Lớp 1 – Tóm tắt

- Chưa tìm thấy khác biệt có ý nghĩa về mức căng thẳng (PSS-10) giữa các nhóm khối lớp (*p* = ,374).
- η² = ,01: mức ảnh hưởng nhỏ.

### Lớp 2 – Chi tiết

**Phép phân tích này để làm gì**

- One-way ANOVA so sánh trung bình mức căng thẳng (PSS-10) giữa 3 nhóm khối lớp trong một lần kiểm định, thay vì làm nhiều t-test (làm nhiều lần sẽ tăng khả năng báo động giả).

**Kiểm tra điều kiện**

- Levene's test có *p* = ,030 ≤ ,05: phương sai các nhóm không đồng nhất. Bạn đọc bảng **Robust Tests (Welch)** và dùng kiểm định sau **Games-Howell**.

**Đọc kết quả**

- Kiểm định Welch: *F*(2; 123,28) = 0,99; *p* = ,374.
- Vì *p* > ,05 nên chưa đủ bằng chứng để kết luận các nhóm khác nhau. **Không** đọc bảng kiểm định sau để tìm cặp khác biệt.

**Mức ảnh hưởng**

- η² = ,01: mức ảnh hưởng nhỏ.

**Kết luận**

- Chưa tìm thấy khác biệt có ý nghĩa về mức căng thẳng (PSS-10) giữa các nhóm khối lớp (*p* = ,374).

**Mẫu câu báo cáo (APA)**

> Do giả định phương sai đồng nhất bị vi phạm (Levene, *p* = ,030), kiểm định Welch được sử dụng. Kết quả không cho thấy khác biệt có ý nghĩa thống kê về mức căng thẳng (PSS-10) giữa các nhóm khối lớp, *F*(2; 123,28) = 0,99; *p* = ,374.

**Câu hỏi gợi mở**

- Có nhóm nào quá ít người làm kết quả kém nhạy không? Có nên gộp nhóm?
- Kết quả này nói gì về giả thuyết ban đầu của bạn?

**Thuật ngữ**

- *M* (Mean) – trung bình
- *SD* (Standard Deviation) – độ lệch chuẩn: các câu trả lời phân tán quanh trung bình nhiều hay ít
- *F* – trị số kiểm định F: biến thiên giữa các nhóm so với biến thiên trong từng nhóm
- *df* (degrees of freedom) – bậc tự do
- *p* (p-value) – mức ý nghĩa: xác suất thấy khác biệt lớn như vậy nếu thật ra không có khác biệt
- Levene's test – kiểm định phương sai đồng nhất giữa các nhóm
- Welch – cách tính hiệu chỉnh khi phương sai các nhóm khác nhau
- η² (eta squared) – tỷ lệ biến thiên của biến phụ thuộc gắn với việc thuộc nhóm nào
- Post hoc – kiểm định sau: so sánh từng cặp nhóm, đã hiệu chỉnh cho nhiều lần so sánh
- Kiểm định phi tham số – không đòi hỏi phân phối chuẩn (Mann-Whitney U, Wilcoxon, Kruskal-Wallis)
