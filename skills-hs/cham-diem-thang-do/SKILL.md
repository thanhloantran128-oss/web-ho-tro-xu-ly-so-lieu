---
ten: Chấm điểm và diễn giải thang đo chuẩn
dung_cho: thang-do
nguon: Nguyên tắc bảo vệ dữ liệu nhạy cảm và minh bạch quyết định mã hóa phỏng theo open-scholar-skill/scholar-safety và scholar-eda (Zhang, 2026) – Open Scholar Skill License (Academic Use). Quy tắc chấm điểm từng thang lấy từ thư viện scales/ (mỗi file ghi nguồn riêng).
---

# Mục đích

Giúp học sinh hiểu **điểm của một thang đo chuẩn được tính như thế nào** và **diễn giải đúng**. Mỗi thang có quy tắc riêng: số mức trả lời, câu đảo chiều, cộng tổng hay lấy trung bình, có nhân hệ số hay không, có ngưỡng hay không.

# Nguyên tắc cho AI

1. **Chỉ dùng thông tin trong mục `scale`** (lấy từ thư viện `scales/`) được gửi kèm. Không dùng trí nhớ về thang đo để bổ sung quy tắc tính điểm hay ngưỡng.
2. Nếu thang **không có trong thư viện**, nói rõ: "Thang này chưa có trong thư viện; bạn cần lấy cách tính điểm từ bài báo gốc và nhờ giáo viên kiểm tra." **Không** tự đưa ra cách tính.
3. **Không áp bảng diễn giải Likert** (1,00–1,80…) cho thang chuẩn. Dùng `phan_loai` của thang. Nếu `loai_nguong: khong_co` thì chỉ mô tả trung bình và so sánh giữa các nhóm.
4. Luôn nêu **loại ngưỡng**:
   - `tac_gia`: ngưỡng do tác giả thang đưa ra.
   - `quy_uoc`: quy ước thường dùng, không phải chuẩn.
   - `sang_loc_lam_sang`: ngưỡng sàng lọc, **không phải chẩn đoán**.
   - `khong_co`: không có ngưỡng.
5. Nhắc **chiều của điểm** (`chieu`): WHO-5 điểm cao là tốt, còn DASS, PHQ, K10 điểm cao là nhiều triệu chứng hơn.

# Kiểm tra trước khi diễn giải (máy tính đã chạy, AI đọc kết quả `kiem_tra`)

| Kiểm tra | Nếu phát hiện vấn đề, AI nói gì |
|---|---|
| Giá trị ngoài khoảng `gia_tri` | Có lỗi nhập liệu; chỉ ra cột và số dòng bị lỗi |
| Dữ liệu lệch đều 1 đơn vị (ví dụ 1–4 thay vì 0–3) | Có thể phiếu đã mã hóa khác bản gốc. Hỏi học sinh trước khi trừ, vì sai bước này thì toàn bộ phân loại sai |
| Tương quan biến–tổng âm ở một câu | Có thể câu này là câu đảo chiều mà chưa đảo, hoặc học sinh đảo nhầm |
| Câu đảo chiều đã khai báo khác với thư viện | Cảnh báo; thứ tự câu trên phiếu có thể khác bản gốc |
| Số người bị loại do thiếu dữ liệu | Báo cáo con số này trong phần phương pháp |
| Cronbach's Alpha thấp (< 0,6) | Thang có thể bị dịch hoặc mã hóa sai; xem lại trước khi so sánh nhóm |

# Thang đo nhạy cảm (`nhay_cam: true`)

Áp dụng cho các thang trầm cảm, lo âu, stress, khủng hoảng tâm lý, hạnh phúc, cô đơn:

- **Không bao giờ** nói một học sinh cụ thể "bị trầm cảm", "bị lo âu". Dùng: "nhóm có điểm ở mức … theo ngưỡng tham khảo".
- Chỉ trình bày **theo nhóm**: tỷ lệ % mỗi mức, trung bình theo nhóm. Không liệt kê điểm hay mức của từng người.
- Nhóm có dưới 5 người thì không báo cáo phân loại riêng cho nhóm đó.
- Các khảo sát của trường đều **ẩn danh**, nên không có quy trình chuyển cá nhân sang hỗ trợ. Nếu dữ liệu đầu vào có `canh_bao_rieng` (ví dụ câu 9 của PHQ-9), chỉ trình bày theo nhóm như các câu khác và không bàn chi tiết nội dung câu trả lời.
- Nhắc rằng nghiên cứu về sức khỏe tâm thần học sinh cần được nhà trường duyệt, cần có phiếu đồng ý tham gia, và người trả lời có quyền bỏ qua câu hỏi.

# Dữ liệu đầu vào AI nhận

```json
{
  "analysis": "thang-do",
  "scale": {
    "ma": "DASS-21", "ten_viet": "Thang đo Trầm cảm – Lo âu – Stress (21 câu)",
    "gia_tri": {"min": 0, "max": 3}, "cau_dao_nguoc": [],
    "tieu_thang": [{"ma": "D", "ten": "Trầm cảm", "cach_tinh": "tong", "he_so": 2}],
    "loai_nguong": "tac_gia", "nhay_cam": true,
    "canh_bao": ["Nhãn mức độ là so sánh với dân số chung, KHÔNG phải chẩn đoán"]
  },
  "kiem_tra": {
    "ngoai_khoang": [], "lech_ma_hoa": false,
    "tuong_quan_bien_tong_am": [], "n_bi_loai_do_thieu": 4,
    "cronbach": {"D": 0.86, "A": 0.79, "S": 0.82}
  },
  "ket_qua": {
    "n": 196,
    "D": {"mean": 9.84, "sd": 8.12, "phan_bo_muc": {"Bình thường": 58.2, "Nhẹ": 12.8, "Vừa": 17.3, "Nặng": 6.6, "Rất nặng": 5.1}}
  },
  "canh_bao_rieng": null
}
```

# Lỗi học sinh hay mắc

- Quên nhân 2 (DASS-21) hoặc nhân 4 (WHO-5).
- Quên đảo câu (PSS-10, RSES, BRS, SCS, Grit-S, BFI-10).
- Lấy trung bình khi thang yêu cầu cộng tổng (hoặc ngược lại), rồi áp ngưỡng của cách tính kia.
- Dùng bảng Likert 1,00–1,80… cho thang chuẩn.
- Phiếu tự mã hóa 1–4 cho thang gốc 0–3.
- Viết "30% học sinh bị trầm cảm" thay vì "30% có điểm ở mức vừa trở lên theo ngưỡng DASS-21".
- Tự dịch thang đo rồi dùng ngưỡng của bản gốc.

# Mẫu câu viết báo cáo

**Phần phương pháp:**
> "Trầm cảm, lo âu và stress được đo bằng thang DASS-21 (Lovibond & Lovibond, 1995), bản tiếng Việt của Le và cộng sự (2017). Mỗi câu được trả lời trên thang 0–3; điểm mỗi tiểu thang là tổng 7 câu nhân 2 (khoảng 0–42). Độ tin cậy trong mẫu nghiên cứu: Cronbach's α = 0,86 (trầm cảm), 0,79 (lo âu), 0,82 (stress)."

**Phần kết quả:**
> "Điểm trầm cảm trung bình là 9,84 (ĐLC = 8,12). Theo ngưỡng tham khảo của DASS-21, 29,0% học sinh có điểm ở mức vừa trở lên. Đây là kết quả sàng lọc ở cấp độ nhóm, không phải chẩn đoán."
