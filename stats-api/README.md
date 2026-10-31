# Máy tính thống kê (stats-api)

Máy chủ Python tính toán thống kê. Kết quả trả về đúng định dạng JSON mà các skill trong `../skills-hs/` mô tả, để AI chỉ diễn giải số liệu thật.

## Cài đặt và chạy

Cần Python 3.12.

```bash
cd stats-api
python -m venv .venv
.venv\Scripts\activate          # Windows; macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest                           # chạy kiểm thử
uvicorn app.main:app --reload    # mở http://127.0.0.1:8000/docs để thử API
```

## Giao diện web

Sau khi chạy `uvicorn`, mở http://127.0.0.1:8000. Giao diện là HTML/JS thuần nằm trong thư mục `web/`, chạy chung máy chủ với API nên không cần cài Node.js.

1. **Thiết kế phiếu:** khai báo câu hỏi chung và Likert tự xây dựng, chọn thang đặc thù (hoặc **bỏ qua**), rồi tải file Excel mẫu.
2. **Phân tích dữ liệu:**
   - Tải file lên.
   - Xác nhận đổi chữ sang số và bỏ mã thiếu (nếu có).
   - Soát thang đo và bảng ghép câu – cột.
   - Chọn phép phân tích và xem kết quả: tóm tắt, chi tiết, mẫu câu APA, bảng số liệu.
   - Khung hỏi AI chỉ hiện khi máy chủ có `ANTHROPIC_API_KEY`.

## Các endpoint

| Endpoint | Việc làm |
|---|---|
| `GET /thang-do` | Danh sách thang trong thư viện `../scales/` |
| `POST /xem-truoc` | Tóm tắt cấu trúc cột và gợi ý thang đo (không trả dữ liệu thô) |
| `POST /phan-tich` | Chấm điểm thang đo và chạy phân tích: `mo-ta`, `tan-suat`, `trung-binh`, `t-test`, `anova`, `thang-do` |
| `POST /giai-thich` | AI giải thích bảng kết quả theo bộ skill (cần `ANTHROPIC_API_KEY`) |

## Đánh giá của người dùng

- Người dùng mở phiếu **5 câu** từ nút "✍ Đánh giá web" ở chân trang hoặc dưới mỗi kết quả. Phiếu hỏi về mức độ hữu ích, độ chính xác, việc đối chiếu với SPSS hay phần mềm khác, mức dễ dùng, và góp ý.
- Phiếu **ẩn danh**: không thu tên, email, dữ liệu khảo sát; không lưu địa chỉ IP. Mỗi máy được gửi tối đa 10 lượt mỗi giờ.
- Dữ liệu lưu tại `data/danh-gia.jsonl`, đã được loại khỏi git. Có thể đổi đường dẫn bằng biến môi trường `DANH_GIA_FILE`.
- Xem tổng hợp trên máy chủ: `.venv/Scripts/python xem_danh_gia.py`. Lệnh này in điểm trung bình, phân bố điểm, tỷ lệ chọn 4–5 và góp ý gần đây, đồng thời xuất `danh-gia.csv` để mở bằng Excel.
- Xem từ xa: đặt biến môi trường `DANH_GIA_MA=<mã bí mật>` rồi mở `/danh-gia/tong-hop?ma=<mã bí mật>`. Không đặt mã thì đường dẫn này bị khóa.

## Phần AI giải thích

`POST /giai-thich` nhận JSON như sau:

```json
{"ket_qua": { ...kết quả trả về từ /phan-tich... },
 "cau_hoi": "Kết quả này nghĩa là gì?",
 "lich_su": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

- Chỉ gửi **bảng kết quả**, không gửi dữ liệu thô.
- System prompt gồm `skills-hs/_core.md` và skill tương ứng với phép phân tích (thêm `cham-diem-thang-do` khi có dùng thang đo). Phần này được cache để giảm chi phí cho các lượt hỏi sau.
- Mô hình mặc định là `claude-opus-5-5` với effort `medium`, đổi được qua biến `CLAUDE_MODEL` và `CLAUDE_EFFORT`. Đã bật fallback phía máy chủ (`fallbacks: "default"`): nếu mô hình từ chối nhầm một câu hỏi, Claude tự chuyển sang mô hình dự phòng.
- Giới hạn: câu hỏi tối đa 2.000 ký tự, tối đa 10 lượt hỏi đáp mỗi cuộc trò chuyện.
- Thử gọi thật: đặt `ANTHROPIC_API_KEY` rồi chạy `python thu_giai_thich.py`.

`/phan-tich` nhận `file` (.csv, .xlsx hoặc .sav) và `params` (chuỗi JSON). Ví dụ: chấm điểm PSS-10 rồi so sánh nam và nữ.

```json
{
  "thang_do": [{"ma": "PSS-10", "cot": ["PSS1","PSS2","PSS3","PSS4","PSS5","PSS6","PSS7","PSS8","PSS9","PSS10"]}],
  "analysis": "t-test", "type": "independent", "dv": "PSS-10_TONG", "group": "GioiTinh"
}
```

Câu nhiều lựa chọn xuất từ Google Forms, so sánh theo giới tính:

```json
{"analysis": "nhieu-lua-chon", "dang": "van_ban", "cot": "KenhThongTin", "label": "Kênh tìm thông tin học tập",
 "cac_lua_chon": ["Facebook", "TikTok", "Website, báo điện tử", "Bạn bè, người thân", "YouTube"],
 "nhom": "GioiTinh", "nhom_label": "giới tính"}
```

Nếu mỗi lựa chọn là một cột 0/1, dùng `"dang": "nhi_phan", "cot_lua_chon": [{"cot": "FB", "label": "Facebook"}, …]`.

Thang Likert tự xây dựng:

```json
{"thang_do": [{"ma": "LIKERT", "gia_tri": {"min": 1, "max": 5},
  "bien": [{"ma": "TT", "ten": "Hứng thú học tập", "cot": ["TT1","TT2","TT3","TT4"], "dao": ["TT4"]}]}],
 "analysis": "trung-binh", "variables": [{"name": "TT"}], "scale_points": 5}
```

## Nhận diện thang đo

**A. File mẫu theo đề tài: `POST /mau-nhap-lieu`.** Gửi JSON, nhận về file `.xlsx`.

```json
{"ten_de_tai": "…",
 "cot_chung": [{"ten": "GioiTinh", "loai": "nhom", "lua_chon": ["Nam", "Nữ"]}],
 "likert": {"so_muc": 5, "bien": [{"ma": "TT", "ten": "Hứng thú học tập", "so_cau": 4, "dao": [4]}]},
 "thang_do": ["PSS-10"]}
```

- `thang_do` để trống (hoặc bỏ đi) là **bỏ qua thang đo đặc thù**. Khi đó chỉ cần câu hỏi chung và/hoặc Likert 5–7 mức tự xây dựng.
- Cột của thang đặc thù được đặt tên chuẩn `PSS10_1…PSS10_10` và chặn đúng khoảng giá trị. Cột Likert tự xây dựng đặt tên `TT1…TT4`.
- Cấu hình được lưu trong sheet ẩn `_cau_hinh`. Khi tải file lên `/xem-truoc`, trường `cau_hinh_tu_file_mau` trả về sẵn tham số `thang_do` và `nhieu_lua_chon` để gửi thẳng vào `/phan-tich`. Nếu học sinh đổi tên hoặc xóa cột, cấu hình bị vô hiệu và web chuyển sang gợi ý như với file thường.

**B. File thường (không dùng mẫu).** `/xem-truoc` gom cột thành nhóm theo ba kiểu tên:

| Kiểu tên cột | Ví dụ |
|---|---|
| Số ở cuối | `PSS1`, `DASS21_3`, `TT 4` |
| Google Forms dạng lưới | `Tiêu đề [hàng]`, giữ đúng thứ tự hàng |
| Số ở đầu câu | `1. Tôi…`, `Câu 2: …` |

Sau đó web gợi ý thang khớp số câu và khoảng giá trị. `khop_chinh_xac` là trường hợp tiền tố trùng tên thang và không lệch mã hóa.

**C. Bảng ghép câu – cột (`bang_ghep`).** Có trong gợi ý đầu tiên, trong cấu hình file mẫu và trong mọi báo cáo chấm điểm. Mỗi dòng gồm: câu, cột, tiểu thang, đảo chiều, min/max, n và tương quan biến–tổng. Câu nào có `nghi_sai_vi_tri: true` (vẫn tương quan âm dù đã đảo đúng) thì nhiều khả năng cột đã bị đặt nhầm vị trí câu. Học sinh sửa bằng cách đổi thứ tự trong `cot`.

## Chuẩn bị dữ liệu

- **Đọc file:**
  - CSV: tự nhận dấu ngăn cột (`,` `;` tab), dấu phẩy thập phân và mã chữ UTF-8 / Windows-1258.
  - Excel: đọc sheet "Dữ liệu" nếu có, nếu không thì đọc sheet đầu tiên.
  - Tự bỏ các dòng trống hoàn toàn; chữ tiếng Việt được chuẩn hóa.
- **`/xem-truoc` trả thêm:**
  - `goi_y_ma_hoa_chu`: các cột Likert đang ở dạng chữ, kèm bộ nhãn khớp (đồng ý, tần suất, hài lòng, mức độ).
  - `canh_bao_ma_thieu`: các cột có mã 99, 999… nghi là mã "không trả lời".
- **Sau khi học sinh xác nhận, gửi kèm trong `params`:**
  - `"ma_hoa_chu": [{"cot": ["TT1","TT2"], "bo": "dong_y_5"}]`, hoặc tự khai báo `"bang": {"Đồng ý": 4, …}`.
  - `"ma_thieu": [99, 999]`
- Mọi kết quả `/phan-tich` có trường `canh_bao_du_lieu`. Các cảnh báo này cũng được đưa lên đầu phần lưu ý của lời giải thích.

## Các nguyên tắc tính toán

- **Độ lệch chuẩn** dùng mẫu số n − 1. **Skewness và Kurtosis** dùng công thức hiệu chỉnh, giống SPSS.
- **Levene** dựa trên trung bình (`center="mean"`), giống dòng "Based on Mean" của SPSS.
- **t-test** trả về cả hai dòng Student và Welch, kèm trường `dong_nen_doc` cho biết dòng nào cần đọc.
- **Cohen's d:**
  - Independent: dùng độ lệch chuẩn gộp (pooled SD).
  - Paired: d_z = trung bình hiệu số / độ lệch chuẩn của hiệu số.
  - One-sample: (M − giá trị kiểm định) / SD.
- **ANOVA** tự chọn kiểm định sau theo Levene: Tukey HSD nếu p > 0,05, ngược lại Games-Howell. Kèm Welch, η² và Kruskal-Wallis.
- **Thang đo**:
  - Dữ liệu mã hóa lệch 1 đơn vị: hệ thống dừng lại chờ học sinh xác nhận `dich_chuyen`.
  - Giá trị ngoài khoảng: không tính điểm, trả về số dòng lỗi theo cách đánh số của Excel.
  - Thiếu câu: không tính điểm thang đó cho người thiếu.
  - Chỉ trả kết quả theo nhóm. Câu 9 của PHQ-9 chỉ báo **số người** trả lời > 0.
- Dữ liệu tải lên chỉ được xử lý trong bộ nhớ, không được lưu lại.
