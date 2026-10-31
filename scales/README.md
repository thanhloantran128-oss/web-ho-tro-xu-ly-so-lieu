# Thư viện thang đo

Mỗi file `.yaml` mô tả **cách tính điểm** của một thang đo. Máy tính thống kê Python đọc file này để tính điểm. AI đọc file này để diễn giải đúng ý nghĩa điểm số.

> ⚠️ Thư viện **không chứa nội dung câu hỏi** (nhiều thang có bản quyền nội dung). Học sinh dùng bản tiếng Việt đã được chuẩn hóa từ tài liệu gốc hoặc từ giáo viên hướng dẫn.

## Danh sách

| File | Thang | Số câu | Giá trị | Cách tính | Nhạy cảm |
|---|---|---|---|---|---|
| `likert-tu-xay-dung.yaml` | Thang Likert tự xây dựng (mẫu) | tùy | 1–5 / 1–7 | Trung bình | |
| `dass-21.yaml` | Trầm cảm – Lo âu – Stress | 21 | 0–3 | Tổng từng tiểu thang × 2 | ✔ |
| `phq-9.yaml` | Sàng lọc trầm cảm | 9 | 0–3 | Tổng | ✔ |
| `gad-7.yaml` | Sàng lọc lo âu lan tỏa | 7 | 0–3 | Tổng | ✔ |
| `pss-10.yaml` | Căng thẳng cảm nhận | 10 | 0–4 | Tổng (đảo 4 câu) | ✔ |
| `k10.yaml` | Mức độ sang chấn tâm lý (Kessler) | 10 | 1–5 | Tổng | ✔ |
| `who-5.yaml` | Chỉ số hạnh phúc WHO-5 | 5 | 0–5 | Tổng × 4 | ✔ |
| `scs-26.yaml` | Tự trắc ẩn (bản đầy đủ) | 26 | 1–5 | TB của 6 tiểu thang | |
| `scs-sf.yaml` | Tự trắc ẩn (bản rút gọn) | 12 | 1–5 | TB của 6 tiểu thang | |
| `rses.yaml` | Lòng tự trọng Rosenberg | 10 | 1–4 | Tổng (đảo 5 câu) | |
| `swls.yaml` | Hài lòng với cuộc sống | 5 | 1–7 | Tổng | |
| `brs.yaml` | Khả năng phục hồi (Brief Resilience) | 6 | 1–5 | Trung bình (đảo 3 câu) | |
| `gse.yaml` | Năng lực bản thân tổng quát | 10 | 1–4 | Tổng | |
| `grit-s.yaml` | Sự bền bỉ (Grit rút gọn) | 8 | 1–5 | Trung bình (đảo 4 câu) | |
| `bsmas.yaml` | Nghiện mạng xã hội Bergen | 6 | 1–5 | Tổng | |
| `ucla-3.yaml` | Cô đơn (3 câu) | 3 | 1–3 | Tổng | |
| `bfi-10.yaml` | Tính cách Big Five (10 câu) | 10 | 1–5 | TB từng chiều (đảo 5 câu) | |

## Cấu trúc file

```yaml
ma: PSS-10                       # mã duy nhất
ten_goc: Perceived Stress Scale  # tên tiếng Anh
ten_viet: Thang đo căng thẳng cảm nhận
tac_gia: "Cohen, Kamarck & Mermelstein (1983); Cohen & Williamson (1988)"
khai_niem: căng thẳng            # đo cái gì
so_cau: 10
gia_tri: {min: 0, max: 4}        # khoảng giá trị mỗi câu trong bản gốc
nhan_gia_tri: {0: Không bao giờ, 4: Rất thường xuyên}
cau_dao_nguoc: [4, 5, 7, 8]      # đảo: giá trị_mới = min + max − giá trị_cũ
tieu_thang:                      # bỏ trống nếu chỉ có điểm tổng
  - {ma: D, ten: Trầm cảm, cau: [...], cach_tinh: tong, he_so: 2}
diem_tong:
  cach_tinh: tong                # tong | trung_binh | trung_binh_cac_tieu_thang | khong_co
  he_so: 1                       # nhân thêm sau khi tính (DASS-21 = 2, WHO-5 = 4)
  khoang: [0, 40]
  chieu: cao_hon_la_nhieu_hon    # điểm cao nghĩa là gì
phan_loai:                       # ngưỡng tham khảo; luôn kèm nguon_phan_loai
  - {tu: 0, den: 13, muc: Thấp}
nguon_phan_loai: "..."
loai_nguong: quy_uoc | tac_gia | sang_loc_lam_sang | khong_co
xu_ly_thieu: "..."
nhay_cam: true                   # bật chế độ bảo vệ dữ liệu sức khỏe tâm thần
canh_bao: ["..."]
quyen_su_dung: "..."
ban_tieng_viet: "..."
nguon_xac_minh: ["..."]          # tài liệu đã đối chiếu khi nhập vào thư viện
```

## Quy ước chung của hệ thống

- **Công thức đảo chiều:** `giá trị mới = min + max − giá trị cũ` (thang 1–5: 6 − x; thang 0–4: 4 − x).
- **Dữ liệu thiếu (mặc định của hệ thống, không phải quy định của tác giả):** nếu một người bỏ trống bất kỳ câu nào thuộc một tiểu thang hoặc thang đo, **không tính điểm** tiểu thang hoặc thang đó cho người này, và báo số người bị loại. Các thang có quy định riêng của tác giả ghi trong mục `xu_ly_thieu`.
- **Mã hóa lệch:** nếu dữ liệu nằm ngoài `gia_tri` một khoảng đều (ví dụ 1–4 thay vì 0–3), hệ thống **dừng lại hỏi** học sinh, không tự trừ.
- **Ngưỡng phân loại** chỉ để mô tả nhóm. Với các thang `nhay_cam: true`, **không hiển thị phân loại theo từng cá nhân**.

## Cách bổ sung thang mới

1. Lấy cách tính điểm từ **tài liệu của tác giả hoặc bài báo gốc**, không lấy từ trang web tổng hợp.
2. Ghi đầy đủ `nguon_xac_minh`, `quyen_su_dung` và `loai_nguong`.
3. Nhờ giáo viên thứ hai kiểm tra chéo trước khi đưa vào sử dụng.
