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
   | `ANTHROPIC_API_KEY` | Để trống nếu không dùng phần hỏi đáp AI |

5. Bấm **Apply / Deploy**. Lần đầu mất khoảng 3–5 phút để cài thư viện.
6. Khi trạng thái là **Live**, web có địa chỉ dạng `https://web-ho-tro-xu-ly-so-lieu.onrender.com`. Nếu tên đã có người dùng, Render sẽ thêm vài ký tự vào cuối địa chỉ.

## Bước 3 – Kiểm tra

1. Mở địa chỉ web, thử tải [`sample-data/khao-sat-mau.csv`](sample-data/khao-sat-mau.csv) lên và chạy một phép phân tích.
2. Bấm **✍ Đánh giá web**, gửi một phiếu thử. Kiểm tra bảng tính Google đã có dòng mới (xóa dòng thử sau đó).

## Lưu ý khi dùng gói miễn phí

- Sau **15 phút** không ai dùng, web "ngủ". Người mở đầu tiên sau đó phải chờ khoảng **30–60 giây**. Trước buổi học, giáo viên nên mở web trước vài phút.
- Mỗi khi bạn đẩy code mới lên nhánh `main` trên GitHub, Render **tự cập nhật** web.
- Dữ liệu học sinh tải lên chỉ xử lý trong bộ nhớ và không lưu lại. Phiếu đánh giá chỉ nằm trong bảng tính Google của bạn.
