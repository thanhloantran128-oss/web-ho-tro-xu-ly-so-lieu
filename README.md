# Web hỗ trợ xử lý số liệu

Website giúp **học sinh THPT xử lý số liệu khảo sát** trong nghiên cứu khoa học hành vi: thiết kế phiếu, nhập liệu, kiểm tra thang đo, chạy phép thống kê và đọc kết quả. Mỗi kết quả có lời giải thích tiếng Việt và mẫu câu viết báo cáo theo chuẩn APA.

> ⚠️ Kết quả dùng để tham khảo, vui lòng xin thêm ý kiến của giáo viên hoặc đối chiếu cùng các phần mềm thống kê khác.

## Tính năng

| Nhóm | Nội dung |
|---|---|
| **Thiết kế phiếu** | Khai báo câu hỏi chung, thang Likert 5/7 mức, chọn thang đo chuẩn (hoặc bỏ qua). Tải về file Excel mẫu có kiểm tra giá trị nhập |
| **Đọc dữ liệu** | `.xlsx`, `.csv` (kể cả CSV kiểu Excel tiếng Việt), `.sav` (SPSS), file xuất từ Google Forms. Tự đổi nhãn Likert chữ sang số và phát hiện mã thiếu 99/999 (đều chờ người dùng xác nhận) |
| **Loại thang đo** | Đề xuất loại cho từng câu: định danh, thứ bậc, Likert, định lượng, nhiều lựa chọn, bỏ qua. Mọi phép phân tích dùng đúng loại đã khai báo |
| **Thang đo chuẩn** | 16 thang (DASS-21, PHQ-9, GAD-7, PSS-10, SCS, Rosenberg, SWLS, BSMAS…), đảo câu, nhân hệ số, Cronbach's α, bảng ghép câu – cột phát hiện câu đặt sai vị trí |
| **Phép phân tích** | Thống kê mô tả, tần suất, câu nhiều lựa chọn, trung bình – độ lệch chuẩn, t-test (3 loại), One-way ANOVA (Welch, Tukey, Games-Howell), bảng chéo Chi-square/Fisher, tương quan Pearson/Spearman, kèm kiểm định phi tham số |
| **Ràng buộc** | Chặn hoặc cảnh báo khi dùng sai loại thang đo (ví dụ t-test với biến định danh), kèm giải thích và phép thay thế |
| **Giải thích** | Hai lớp (tóm tắt và chi tiết), độ lớn ảnh hưởng, mẫu câu APA, câu hỏi gợi mở. Không cần AI; hỏi đáp AI là tùy chọn |
| **Kiến thức thống kê** | 36 mục giải thích các chỉ số và lý do cần thực hiện, bảng "Chọn phép phân tích nào?" |
| **Tiện ích** | Chép bảng sang Word/Excel, phiếu đánh giá ẩn danh 5 câu |

## Chạy trên máy

Cần **Python 3.12**.

```bash
cd stats-api
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt      # macOS/Linux: .venv/bin/python
.venv/Scripts/python -m pytest                               # kiểm thử
.venv/Scripts/python -m uvicorn app.main:app --port 8000
```

Mở http://localhost:8000. Muốn thử nhanh, dùng dữ liệu mô phỏng trong [`sample-data/khao-sat-mau.csv`](sample-data/khao-sat-mau.csv).

Phần hỏi đáp AI chỉ bật khi đặt biến môi trường `ANTHROPIC_API_KEY` (xem [`stats-api/.env.example`](stats-api/.env.example)). Không có khóa thì web vẫn chạy đầy đủ với phần giải thích tự động.

## Cấu trúc thư mục

| Thư mục | Nội dung |
|---|---|
| [`stats-api/`](stats-api/README.md) | Máy chủ Python (FastAPI): tính toán thống kê, API, giao diện web trong `web/`, kiểm thử trong `tests/` |
| [`giai-thich/`](giai-thich/README.md) | Câu mẫu giải thích, ràng buộc thang đo, nội dung tab kiến thức (YAML, sửa được không cần biết lập trình) |
| [`scales/`](scales/README.md) | Thư viện quy tắc tính điểm 16 thang đo chuẩn (không chứa nội dung câu hỏi) |
| [`skills-hs/`](skills-hs/_core.md) | Bộ skill hướng dẫn AI giải thích kết quả cho học sinh |
| [`mau-nhap-lieu/`](mau-nhap-lieu/) | File Excel mẫu nhập liệu |
| [`sample-data/`](sample-data/) | Dữ liệu **mô phỏng** để chạy thử |

## Quyền riêng tư

- Dữ liệu tải lên chỉ được xử lý trong bộ nhớ cho từng lần phân tích và **không được lưu lại**.
- Phần hỏi đáp AI chỉ gửi **bảng kết quả đã tính**, không gửi dữ liệu thô.
- Phiếu đánh giá ẩn danh, không lưu địa chỉ IP.
- Với thang đo sức khỏe tinh thần, kết quả chỉ trình bày theo nhóm, không gắn nhãn cá nhân.

## Lưu ý về thang đo chuẩn

Thư viện chỉ lưu **cách tính điểm**, không chứa nội dung câu hỏi. Một số thang có điều kiện sử dụng riêng; nhiều thang còn ghi "cần kiểm tra" về quyền sử dụng và bản tiếng Việt đã chuẩn hóa. Hãy dùng bản dịch đã được kiểm định và trao đổi với giáo viên hướng dẫn, nhất là với các thang về sức khỏe tinh thần.

## Giấy phép và ghi nguồn

- Phần do dự án phát triển: **[Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](LICENSE)**. Bạn được dùng, sửa và chia sẻ cho mục đích **phi thương mại**, kèm ghi nguồn.
- Bộ skill và một số nguyên tắc phân tích phỏng theo **Open Scholar Skill**, phát hành theo Open Scholar Skill License (Academic Use). Toàn văn giấy phép gốc nằm trong [THIRD_PARTY_LICENSE](THIRD_PARTY_LICENSE). Mọi sử dụng thương mại cần xin phép tác giả gốc.

> Zhang, Y. (2026). Open Scholar Skill. *Chinese Sociological Review*. https://doi.org/10.1080/21620555.2026.2707167 · https://github.com/joshzyj/open-scholar-skill

Các thang đo chuẩn thuộc bản quyền của tác giả tương ứng; nguồn của từng thang được ghi trong file `scales/*.yaml`.
