# Thư viện giải thích tự động (không dùng AI)

Mỗi kết quả từ `/phan-tich` có thêm trường `giai_thich`, gồm:

| Trường | Nội dung |
|---|---|
| `tom_tat` | **Lớp 1**: 1–3 câu kết luận chính |
| `chi_tiet` | **Lớp 2**: các mục *Phép phân tích này để làm gì*, *Kiểm tra điều kiện*, *Đọc kết quả*, *Mức ảnh hưởng*, *Kết luận* |
| `bao_cao` | Mẫu câu viết báo cáo theo APA (dấu phẩy thập phân; bỏ số 0 trước *p*, *r*, α, η²) |
| `canh_bao` | Các lưu ý (nhóm nhỏ, phân phối lệch, kiểm định phi tham số cho kết quả khác…) |
| `goi_mo` | Câu hỏi gợi mở cho học sinh |
| `thuat_ngu` | Thuật ngữ tiếng Anh kèm giải nghĩa tiếng Việt |

## Sửa lời văn

| File | Dùng cho |
|---|---|
| `chung.yaml` | Định dạng số, các ngưỡng (*d*, η², Cronbach, skewness…), tiêu đề mục, thuật ngữ |
| `mo-ta.yaml`, `tan-suat.yaml`, `trung-binh.yaml` | Thống kê mô tả |
| `t-test.yaml`, `anova.yaml` | So sánh nhóm |
| `thang-do.yaml` | Chấm điểm thang đo |
| `nhieu-lua-chon.yaml` | Câu hỏi chọn nhiều đáp án |

Cách sửa:

1. Sửa câu trong dấu ngoặc kép. **Giữ nguyên** các chỗ `{…}`, vì đó là chỗ điền số tự động. Danh sách biến dùng được ghi ở đầu mỗi file.
2. Câu bắt đầu bằng `*` (chữ nghiêng) phải nằm trong dấu ngoặc kép.
3. Thêm câu hỏi gợi mở: thêm một dòng `- "…"` vào mục `goi_mo`.
4. Kiểm tra sau khi sửa (trong thư mục `stats-api`):

```bash
.venv/Scripts/python -m pytest
```

```bash
.venv/Scripts/python tao_vi_du_giai_thich.py
```

Lệnh thứ hai cập nhật file [VI_DU.md](VI_DU.md) để bạn đọc lại toàn bộ lời giải thích trên dữ liệu mẫu.
