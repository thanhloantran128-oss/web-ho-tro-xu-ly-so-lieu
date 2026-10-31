---
ten: Kiểm định t (t-test)
dung_cho: t-test
nguon: Nguyên tắc kiểm tra điều kiện trước khi diễn giải và báo cáo độ lớn ảnh hưởng phỏng theo open-scholar-skill/scholar-analyze (Zhang, 2026) – Open Scholar Skill License (Academic Use). Phần hướng dẫn đọc bảng SPSS biên soạn mới cho học sinh THPT.
---

# Mục đích

So sánh **trung bình** để xem khác biệt là thật hay chỉ do ngẫu nhiên của việc chọn mẫu.

# Bước 1 – Chọn đúng loại t-test

| Câu hỏi nghiên cứu | Loại t-test | Ví dụ |
|---|---|---|
| Trung bình của mẫu có khác một giá trị cho trước không? | **One-sample t-test** | Điểm niềm tin trung bình có khác mức trung lập 3 không? |
| Hai **nhóm người khác nhau** có trung bình khác nhau không? | **Independent-samples t-test** | Nam và nữ có mức nhận biết thương hiệu khác nhau không? |
| **Cùng một nhóm người** đo hai lần (hoặc trả lời hai câu cùng thang đo) có khác nhau không? | **Paired-samples t-test** | Điểm trước và sau buổi ngoại khóa của cùng một lớp |

Nếu có **từ 3 nhóm trở lên** thì không dùng t-test mà chuyển sang **ANOVA**.

# Loại thang đo phù hợp (ràng buộc bắt buộc)

| Vai trò | Được dùng | Không được dùng → phép thay thế |
|---|---|---|
| **Biến phụ thuộc** (biến được so sánh trung bình) | Thang **khoảng / tỷ lệ**: điểm số, số giờ, tuổi; **điểm trung bình của thang Likert nhiều câu** (đã kiểm định Cronbach) | Biến **định danh** (giới tính, lớp) → Tần suất / Chi-square. Biến **nhị phân** 0/1 → so sánh tỷ lệ bằng Chi-square |
| | ⚠ **Một câu Likert đơn lẻ / biến thứ bậc ít mức**: về lý thuyết là thang thứ bậc, chỉ dùng t-test như tham khảo | Ưu tiên điểm cả thang, hoặc đọc kiểm định phi tham số (Mann-Whitney U, Wilcoxon) |
| **Biến nhóm** (Independent) | Biến **định danh hoặc thứ bậc** có **đúng 2 nhóm** | Biến số đo liên tục (số giờ, điểm) → chia nhóm trước hoặc dùng tương quan. Từ 3 nhóm → ANOVA |
| **Hai lần đo** (Paired) | Hai cột của **cùng một biến, cùng thang đo**, trên **cùng những người** | Hai biến khác nhau (ví dụ điểm Toán và mức căng thẳng) không so sánh bằng Paired t-test |
| **Giá trị so sánh** (One-sample) | Nằm trong khoảng của thang, ví dụ 3 với Likert 5 mức, 4 với Likert 7 mức | — |

Hệ thống web tự kiểm tra các ràng buộc này. Lỗi nghiêm trọng thì không chạy; trường hợp ⚠ thì vẫn chạy nhưng kèm cảnh báo. Khi giải thích, AI phải nhắc lại cảnh báo này nếu có trong `kiem_tra_dieu_kien`.

# Bước 2 – Kiểm tra điều kiện

1. **Biến phụ thuộc là biến định lượng** (điểm, giờ, trung bình thang Likert). Không dùng cho biến định danh.
2. **Quan sát độc lập**: mỗi người chỉ trả lời một lần (riêng paired t-test cho phép hai lần đo trên cùng người, nhưng các cặp phải độc lập với nhau).
3. **Phân phối xấp xỉ chuẩn** trong mỗi nhóm (với paired thì xét phân phối của **hiệu số**). Khi mỗi nhóm có từ khoảng 30 người trở lên, t-test khá "chịu đựng" được việc lệch chuẩn vừa phải. Nếu nhóm nhỏ (dưới 30) **và** phân phối lệch mạnh hoặc có giá trị cực đoan thì dùng kiểm định phi tham số:
   - One-sample → **Wilcoxon signed-rank** (một mẫu)
   - Independent → **Mann-Whitney U**
   - Paired → **Wilcoxon signed-rank**
4. **Không có giá trị cực đoan bất thường**. Kiểm tra bằng boxplot.
5. **Riêng Independent t-test: kiểm tra phương sai bằng nhau** bằng kiểm định Levene (xem bước 3).

# Bước 3 – Đọc bảng kết quả (theo SPSS)

## Independent-samples t-test

**Bảng Group Statistics**: N, Mean, Std. Deviation của từng nhóm. Dùng để biết **nhóm nào cao hơn**.

**Bảng Independent Samples Test** có 2 dòng. Phải chọn đúng dòng:

1. Nhìn **Levene's Test → Sig.**
   - Sig. **> 0,05** → phương sai hai nhóm coi như bằng nhau → đọc dòng **"Equal variances assumed"**.
   - Sig. **≤ 0,05** → phương sai khác nhau → đọc dòng **"Equal variances not assumed"** (kiểm định Welch, df thường là số lẻ).
2. Trên dòng đã chọn, nhìn **Sig. (2-tailed)** (SPSS bản mới ghi là **Two-Sided p**):
   - **≤ 0,05** → bác bỏ H0 → hai nhóm khác biệt có ý nghĩa thống kê.
   - **> 0,05** → chưa đủ bằng chứng để kết luận hai nhóm khác nhau.
3. **Mean Difference** và **95% Confidence Interval**: khoảng tin cậy **không chứa 0** thì tương ứng với p < 0,05.

Ghi chú cho AI: nhiều tài liệu hiện nay khuyên luôn dùng dòng Welch ("not assumed") vì nó an toàn trong cả hai trường hợp. Khi học sinh dùng quy tắc Levene theo giáo trình thì vẫn chấp nhận, có thể nhắc thêm thông tin này.

## One-sample t-test

- **Test Value** = giá trị so sánh (ví dụ 3).
- Đọc **t, df, Sig. (2-tailed), Mean Difference** (= trung bình mẫu − Test Value). Mean Difference dương nghĩa là cao hơn giá trị so sánh.

## Paired-samples t-test

- **Paired Samples Statistics**: trung bình từng lần đo.
- **Paired Samples Test**: Mean (trung bình của hiệu số), t, df, Sig. (2-tailed).
- Bảng **Paired Samples Correlations** chỉ để tham khảo, **không phải** kết quả kiểm định khác biệt.

# Bước 4 – Độ lớn ảnh hưởng (Cohen's d)

p chỉ cho biết khác biệt có "thật" không, còn **d cho biết khác biệt lớn hay nhỏ**. Với mẫu lớn, chênh lệch rất nhỏ cũng có thể cho p < 0,05.

| \|d\| | Mức ảnh hưởng (quy ước Cohen) |
|---|---|
| < 0,2 | Rất nhỏ, gần như không đáng kể |
| 0,2 – < 0,5 | Nhỏ |
| 0,5 – < 0,8 | Trung bình |
| ≥ 0,8 | Lớn |

SPSS từ bản 27 có bảng "Effect Sizes" với Cohen's d. Nếu không có d trong dữ liệu đầu vào thì nói rõ là chưa có, **không tự tính**.

# Một phía hay hai phía?

Mặc định dùng **hai phía (2-tailed)**. Chỉ dùng một phía khi giả thuyết có hướng **được viết ra trước khi thu dữ liệu** (ví dụ "nhóm A cao hơn nhóm B"). Không được đổi sang một phía sau khi thấy p hai phía hơi lớn hơn 0,05.

# Dữ liệu đầu vào AI nhận

```json
{
  "analysis": "t-test",
  "type": "independent | one-sample | paired",
  "dv": {"name": "NB", "label": "Nhận biết thương hiệu (TB thang 1–5)"},
  "groups": [
    {"label": "Nam", "n": 92, "mean": 3.52, "sd": 0.71},
    {"label": "Nữ", "n": 108, "mean": 3.78, "sd": 0.64}
  ],
  "test_value": null,
  "levene": {"F": 1.84, "p": 0.177},
  "student": {"t": -2.72, "df": 198, "p": 0.007, "mean_diff": -0.26, "ci95": [-0.45, -0.07]},
  "welch":   {"t": -2.70, "df": 185.1, "p": 0.008, "mean_diff": -0.26, "ci95": [-0.45, -0.07]},
  "cohens_d": -0.39,
  "normality": {"skewness_by_group": [0.42, -0.31]},
  "nonparametric": {"test": "Mann-Whitney U", "U": 4012.5, "p": 0.009}
}
```

Với one-sample: `groups` có 1 phần tử, `test_value` là số, không có `levene`/`welch`. Với paired: `groups` là 2 lần đo, thêm `diff_mean`, `diff_sd`, không có `levene`.

# Lỗi học sinh hay mắc

- Đọc nhầm Sig. của Levene thành kết quả t-test. Levene chỉ để chọn dòng.
- Dùng independent t-test cho dữ liệu đo trước–sau trên cùng người (phải dùng paired).
- Làm nhiều t-test giữa từng cặp khi có 3 nhóm trở lên (phải dùng ANOVA).
- Kết luận "nam và nữ giống nhau" khi p > 0,05. Đúng ra phải nói "chưa tìm thấy khác biệt có ý nghĩa".
- Chỉ báo cáo p, không báo cáo trung bình từng nhóm, t, df và d.
- Kết luận nhân quả: "vì là nữ nên nhận biết cao hơn".

# Mẫu câu viết báo cáo

**Independent:**
> "Kết quả kiểm định Independent-samples t-test cho thấy học sinh nữ (M = 3,78; ĐLC = 0,64) có mức nhận biết thương hiệu cao hơn học sinh nam (M = 3,52; ĐLC = 0,71), khác biệt có ý nghĩa thống kê, t(198) = −2,72; p = 0,007; d = 0,39 (mức ảnh hưởng nhỏ). Kiểm định Levene cho thấy phương sai hai nhóm đồng nhất (p = 0,177)."

**One-sample:**
> "Điểm niềm tin trung bình (M = 3,74; ĐLC = 0,69) cao hơn có ý nghĩa so với mức trung lập 3, t(199) = 15,17; p < 0,001."

**Không có ý nghĩa:**
> "Chưa tìm thấy khác biệt có ý nghĩa thống kê về mức nhận biết giữa học sinh khối 10 và khối 11, t(138) = 1,12; p = 0,265."
