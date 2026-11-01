# Hướng dẫn đưa web chạy trực tuyến (Render + Google Sheets)

Tổng thời gian khoảng 20 phút. Bạn cần một tài khoản Google và tài khoản GitHub (đã có kho `web-ho-tro-xu-ly-so-lieu`).

## Bước 1 – Google Sheets lưu phiếu đánh giá

Gói miễn phí của Render xóa ổ đĩa mỗi khi máy chủ khởi động lại, nên phiếu đánh giá được gửi sang Google Sheets để lưu lâu dài.

1. Vào https://sheets.new để tạo bảng tính mới, đặt tên ví dụ **"Đánh giá web xử lý số liệu"**.
2. Trên bảng tính, chọn menu **Tiện ích mở rộng → Apps Script** (Extensions → Apps Script).
3. Xóa đoạn mã có sẵn, dán **toàn bộ** nội dung file [`google-sheets/danh-gia.gs`](google-sheets/danh-gia.gs).
4. Ở dòng `const MA_BI_MAT = '...'`, đổi thành một chuỗi bí mật của riêng bạn (ví dụ 20 ký tự chữ và số ngẫu nhiên). **Ghi lại chuỗi này** để dùng ở bước 2.
5. Bấm **Lưu** (biểu tượng đĩa mềm).
6. Bấm **Triển khai → Tùy chọn triển khai mới** (Deploy → New deployment):
   - Chọn loại (bánh răng): **Ứng dụng web** (Web app).
   - *Thực thi với tư cách* (Execute as): **Tôi** (Me).
   - *Người có quyền truy cập* (Who has access): **Bất kỳ ai** (Anyone).
   - Bấm **Triển khai**. Google sẽ hỏi cấp quyền; chọn tài khoản của bạn → *Nâng cao* → *Đi tới… (không an toàn)* → *Cho phép*. Cảnh báo này xuất hiện vì đoạn mã do chính bạn tạo, chưa được Google xác minh.
7. Sao chép **URL ứng dụng web** (dạng `https://script.google.com/macros/s/…/exec`).
8. Kiểm tra: dán URL đó vào trình duyệt. Thấy dòng `{"ok":true, … "đang hoạt động"}` là đúng.

Khi có phiếu đầu tiên, bảng tính tự tạo sheet **Phiếu** (mỗi phiếu một dòng) và **Tổng hợp** (điểm trung bình, tỷ lệ chọn 4–5, thống kê đối chiếu với phần mềm khác).

> Mỗi lần sửa mã Apps Script, phải **Triển khai → Quản lý các bản triển khai → Sửa → Phiên bản mới** thì thay đổi mới có hiệu lực, và URL giữ nguyên.

## Bước 2 – Render chạy web

1. Vào https://render.com, chọn **Get Started** và **đăng nhập bằng GitHub** (tài khoản `thanhloantran128-oss`).
2. Trên bảng điều khiển, chọn **New → Blueprint**.
3. Cho phép Render truy cập kho **web-ho-tro-xu-ly-so-lieu**, rồi chọn kho này. Render tự đọc file [`render.yaml`](render.yaml).
4. Render hỏi giá trị cho các biến môi trường:

   | Biến | Giá trị |
   |---|---|
   | `DANH_GIA_GOOGLE_URL` | URL ứng dụng web ở bước 1.7 |
   | `DANH_GIA_GOOGLE_MA` | Chuỗi bí mật ở bước 1.4 (phải giống hệt) |
   | `GOATCOUNTER_CODE` | Tên trang GoatCounter ở bước 4 (để trống nếu chưa làm) |
   | `ANTHROPIC_API_KEY` | Để trống nếu không dùng phần hỏi đáp AI |

5. Bấm **Apply / Deploy**. Lần đầu mất khoảng 3–5 phút để cài thư viện.
6. Khi trạng thái là **Live**, web có địa chỉ dạng `https://web-ho-tro-xu-ly-so-lieu.onrender.com`. Nếu tên đã có người dùng, Render sẽ thêm vài ký tự vào cuối địa chỉ.

## Bước 3 – Kiểm tra

1. Mở địa chỉ web, thử tải [`sample-data/khao-sat-mau.csv`](sample-data/khao-sat-mau.csv) lên và chạy một phép phân tích.
2. Bấm **✍ Đánh giá web**, gửi một phiếu thử. Kiểm tra bảng tính Google đã có dòng mới (xóa dòng thử sau đó).

## Bước 4 – Đếm số người sử dụng web

Web đếm theo hai cách, cả hai đều **ẩn danh**: không cookie, không địa chỉ IP, không dữ liệu khảo sát.

### 4a. Lượt phân tích – tự động trong Google Sheets

Mỗi lần có người chạy phân tích thành công, máy chủ ghi một dòng vào sheet **"Lượt dùng"**: thời gian, phép phân tích, số dòng dữ liệu, có dùng thang đo chuẩn hay không, và một *mã trình duyệt ẩn danh* (chuỗi ngẫu nhiên trình duyệt tự tạo, dùng để ước tính số người khác nhau).

Sheet **"Thống kê lượt dùng"** tự tính:
- số lượt phân tích và số người dùng (ước tính) từ trước đến nay, 7 ngày qua, 30 ngày qua;
- số lượt và số người theo từng tháng (12 tháng gần nhất);
- số lượt theo từng phép phân tích (cột E).

Cách bật: dùng chung Web App ở bước 1, chỉ cần cập nhật đoạn mã.
1. Mở bảng tính → **Tiện ích mở rộng → Apps Script**.
2. Dán **toàn bộ** đoạn mã mới trong [`google-sheets/danh-gia.gs`](google-sheets/danh-gia.gs) đè lên mã cũ, rồi **đổi lại `MA_BI_MAT`** thành chuỗi bí mật của bạn (giống trên Render).
3. **Lưu** → **Triển khai → Quản lý các bản triển khai → ✏️ Sửa → Phiên bản: Phiên bản mới → Triển khai**. URL giữ nguyên.
4. Nên kiểm tra **Tệp → Cài đặt → Múi giờ** của bảng tính là *(GMT+07:00) Bangkok/Hà Nội* để thời gian và thống kê theo ngày đúng giờ Việt Nam.

Hai sheet "Lượt dùng" và "Thống kê lượt dùng" tự xuất hiện sau lượt phân tích đầu tiên.

> "Người dùng (ước tính)" đếm số trình duyệt khác nhau: một người dùng hai máy được tính hai lần; người dùng chế độ ẩn danh hoặc xóa dữ liệu trình duyệt cũng được tính như người mới. Con số dùng để thấy xu hướng, không phải số chính xác.

### 4b. Lượt truy cập – GoatCounter

GoatCounter cho biết bao nhiêu lượt mở web, từ thiết bị nào, vào ngày nào, và cả số lượt từng phép phân tích (mục *Events*).

1. Vào https://www.goatcounter.com/signup, chọn **Code** (tên trang), ví dụ `xu-ly-so-lieu` → trang thống kê sẽ ở `https://xu-ly-so-lieu.goatcounter.com`. Nhập email, mật khẩu do bạn tự đặt.
2. Trên Render: **dịch vụ → Environment → Add Environment Variable**: `GOATCOUNTER_CODE` = tên trang (chỉ phần `xu-ly-so-lieu`, không có `https://` hay `.goatcounter.com`) → **Save Changes**.
3. Sau khi Render khởi động lại, mở web vài lần rồi vào trang GoatCounter để xem. Số liệu có thể chậm vài phút.

GoatCounter miễn phí cho dự án phi thương mại, không dùng cookie nên không cần bảng hỏi đồng ý cookie.

## Lưu ý khi dùng gói miễn phí

- Sau **15 phút** không ai dùng, web "ngủ". Người mở đầu tiên sau đó phải chờ khoảng **30–60 giây**. Trước buổi học, giáo viên nên mở web trước vài phút.
- Mỗi khi bạn đẩy code mới lên nhánh `main` trên GitHub, Render **tự cập nhật** web.
- Dữ liệu học sinh tải lên chỉ xử lý trong bộ nhớ và không lưu lại. Phiếu đánh giá chỉ nằm trong bảng tính Google của bạn.

## Phương án khác – chạy trên Vercel

Kho đã có sẵn [`vercel.json`](vercel.json), [`api/index.py`](api/index.py) và [`requirements.txt`](requirements.txt) ở thư mục gốc.

1. Trên Vercel: **Add New → Project**, chọn kho `web-ho-tro-xu-ly-so-lieu`.
2. **Root Directory: để trống** (thư mục gốc của kho), **không** chọn `stats-api`. Nếu chọn `stats-api`, các thư mục `scales/`, `giai-thich/`, `skills-hs/` nằm ngoài sẽ không được đóng gói và mọi API báo lỗi 500 (`FUNCTION_INVOCATION_FAILED`).
3. **Framework Preset: Other**. Không cần điền Build Command hay Output Directory.
4. **Environment Variables**: `DANH_GIA_GOOGLE_URL`, `DANH_GIA_GOOGLE_MA`, `GOATCOUNTER_CODE` (giống trên Render).
5. Deploy.

Khác biệt so với Render:
- Không "ngủ" như Render, nhưng lần gọi đầu sau một thời gian có thể chậm vài giây (khởi động hàm).
- File tải lên tối đa khoảng **4 MB** (giới hạn của Vercel).
- Ổ đĩa không lưu lâu dài, nên phiếu đánh giá và lượt dùng **phải** dùng Google Sheets.
