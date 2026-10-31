/**
 * Nhận phiếu đánh giá và lượt dùng từ web, ghi vào Google Sheets.
 * - Sheet "Phiếu" + "Tổng hợp": phiếu đánh giá 5 câu.
 * - Sheet "Lượt dùng" + "Thống kê lượt dùng": mỗi lần chạy phân tích thành công là một dòng
 *   (không có dữ liệu khảo sát; mã trình duyệt là chuỗi ngẫu nhiên ẩn danh).
 * Cách cài đặt: xem TRIEN_KHAI.md (mục "Bước 1 – Google Sheets").
 *
 * 1. Đổi MA_BI_MAT bên dưới thành một chuỗi ngẫu nhiên của riêng bạn
 *    (dán đúng chuỗi đó vào biến DANH_GIA_GOOGLE_MA trên Render).
 * 2. Triển khai: Deploy → New deployment → Web app → Execute as: Me → Who has access: Anyone.
 */
const MA_BI_MAT = 'DOI-THANH-CHUOI-BI-MAT-CUA-BAN';

const SHEET_PHIEU = 'Phiếu';
const SHEET_TONG_HOP = 'Tổng hợp';
const SHEET_LUOT = 'Lượt dùng';
const SHEET_THONG_KE = 'Thống kê lượt dùng';
const COT_LUOT = ['Thời gian', 'Phép phân tích', 'Số dòng dữ liệu', 'Dùng thang đo chuẩn', 'Mã trình duyệt ẩn danh'];
const COT = ['Thời gian (UTC)', 'Vai trò', 'Phép phân tích', 'Hữu ích (1–5)', 'Chính xác (1–5)',
             'Dễ dùng (1–5)', 'Đối chiếu phần mềm khác', 'Góp ý'];

function doPost(e) {
  let data;
  try {
    data = JSON.parse(e.postData.contents);
  } catch (err) {
    return traVe_({ ok: false, loi: 'Dữ liệu không hợp lệ' });
  }
  if (data.ma !== MA_BI_MAT) return traVe_({ ok: false, loi: 'Sai mã' });

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);   // tránh hai dòng ghi đè cùng lúc
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    if (data.loai === 'luot_dung') ghiLuotDung_(ss, data);
    else ghiPhieu_(ss, data);
  } finally {
    lock.releaseLock();
  }
  return traVe_({ ok: true });
}

/** Mở đường dẫn Web App trên trình duyệt để kiểm tra đã triển khai đúng. */
function doGet() {
  return traVe_({ ok: true, thong_bao: 'Web App nhận phiếu đánh giá và lượt dùng đang hoạt động.' });
}

function ghiPhieu_(ss, data) {
  const sheet = ss.getSheetByName(SHEET_PHIEU) || taoSheetPhieu_(ss);
  sheet.appendRow([
    data.thoi_gian, data.vai_tro, data.phep_phan_tich,
    soHopLe_(data.huu_ich), soHopLe_(data.chinh_xac), soHopLe_(data.de_dung),
    data.doi_chieu, String(data.gop_y || '').slice(0, 1000),
  ]);
  if (!ss.getSheetByName(SHEET_TONG_HOP)) taoSheetTongHop_(ss);
}

function ghiLuotDung_(ss, data) {
  const sheet = ss.getSheetByName(SHEET_LUOT) || taoSheetLuot_(ss);
  const soDong = Number(data.so_dong);
  sheet.appendRow([
    new Date(),   // theo múi giờ của bảng tính (Tệp → Cài đặt)
    String(data.phep_phan_tich || '').slice(0, 40),
    Number.isFinite(soDong) ? soDong : '',
    data.thang_do_chuan === 'Có' ? 'Có' : 'Không',
    /^[a-z0-9]{16,40}$/.test(data.ma_trinh_duyet || '') ? data.ma_trinh_duyet : '',
  ]);
  if (!ss.getSheetByName(SHEET_THONG_KE)) taoSheetThongKe_(ss);
}

function soHopLe_(x) {
  const n = Number(x);
  return n >= 1 && n <= 5 ? n : '';
}

function taoSheetPhieu_(ss) {
  const sheet = ss.insertSheet(SHEET_PHIEU);
  sheet.appendRow(COT);
  sheet.getRange(1, 1, 1, COT.length).setFontWeight('bold').setBackground('#0b2a5b').setFontColor('#ffffff');
  sheet.setFrozenRows(1);
  sheet.setColumnWidth(8, 420);
  return sheet;
}

function taoSheetTongHop_(ss) {
  const s = ss.insertSheet(SHEET_TONG_HOP);
  const P = "'" + SHEET_PHIEU + "'!";
  const dong = [
    ['Tiêu chí', 'Điểm trung bình', 'Số phiếu', 'Tỷ lệ chọn 4–5'],
    ['Hữu ích', `=IFERROR(AVERAGE(${P}D2:D),"")`, `=COUNT(${P}D2:D)`, `=IFERROR(COUNTIF(${P}D2:D,">=4")/COUNT(${P}D2:D),"")`],
    ['Chính xác', `=IFERROR(AVERAGE(${P}E2:E),"")`, `=COUNT(${P}E2:E)`, `=IFERROR(COUNTIF(${P}E2:E,">=4")/COUNT(${P}E2:E),"")`],
    ['Dễ dùng', `=IFERROR(AVERAGE(${P}F2:F),"")`, `=COUNT(${P}F2:F)`, `=IFERROR(COUNTIF(${P}F2:F,">=4")/COUNT(${P}F2:F),"")`],
    ['', '', '', ''],
    ['Đối chiếu với phần mềm khác', 'Số phiếu', '', ''],
    ['Khớp hoàn toàn', `=COUNTIF(${P}G2:G,"Khớp hoàn toàn")`, '', ''],
    ['Khớp phần lớn', `=COUNTIF(${P}G2:G,"Khớp phần lớn")`, '', ''],
    ['Không khớp', `=COUNTIF(${P}G2:G,"Không khớp")`, '', ''],
    ['Chưa đối chiếu', `=COUNTIF(${P}G2:G,"Chưa đối chiếu")`, '', ''],
  ];
  const range = s.getRange(1, 1, dong.length, 4);
  range.setValues(dong.map((r) => r.map((c) => (String(c).startsWith('=') ? '' : c))));
  dong.forEach((r, i) => r.forEach((c, j) => { if (String(c).startsWith('=')) s.getRange(i + 1, j + 1).setFormula(c); }));
  s.getRange('B2:B4').setNumberFormat('0.00');
  s.getRange('D2:D4').setNumberFormat('0.0%');
  [1, 6].forEach((row) => s.getRange(row, 1, 1, 4).setFontWeight('bold').setBackground('#e5ecf7'));
  s.setColumnWidth(1, 220);
}

function taoSheetLuot_(ss) {
  const sheet = ss.insertSheet(SHEET_LUOT);
  sheet.appendRow(COT_LUOT);
  sheet.getRange(1, 1, 1, COT_LUOT.length).setFontWeight('bold').setBackground('#0b2a5b').setFontColor('#ffffff');
  sheet.setFrozenRows(1);
  sheet.getRange('A:A').setNumberFormat('dd/mm/yyyy hh:mm');
  sheet.setColumnWidth(1, 150);
  sheet.setColumnWidth(2, 200);
  sheet.setColumnWidth(5, 220);
  return sheet;
}

/** Thống kê tự cập nhật: tổng, 7 và 30 ngày qua, 12 tháng gần nhất, theo từng phép phân tích.
 *  "Người dùng" = số mã trình duyệt khác nhau (gần đúng: một người dùng hai máy tính là hai mã). */
function taoSheetThongKe_(ss) {
  const s = ss.insertSheet(SHEET_THONG_KE);
  const L = "'" + SHEET_LUOT + "'!";
  const A = L + 'A2:A', E = L + 'E2:E';
  const nguoi = (dk) => `=IFERROR(COUNTUNIQUE(FILTER(${E},${E}<>""${dk})),0)`;
  const tom = [
    ['Tổng quan', 'Lượt phân tích', 'Người dùng (ước tính)'],
    ['Từ trước đến nay', `=COUNT(${A})`, nguoi('')],
    ['7 ngày qua', `=COUNTIF(${A},">="&(TODAY()-6))`, nguoi(`,${A}>=TODAY()-6`)],
    ['30 ngày qua', `=COUNTIF(${A},">="&(TODAY()-29))`, nguoi(`,${A}>=TODAY()-29`)],
    ['', '', ''],
    ['Tháng', 'Lượt phân tích', 'Người dùng (ước tính)'],
  ];
  for (let k = 0; k < 12; k++) {
    const r = tom.length + 1;   // dòng của tháng này trên sheet
    const dau = `EOMONTH(TODAY(),${-k - 1})+1`;
    tom.push([`=${dau}`,
      `=COUNTIFS(${A},">="&A${r},${A},"<"&EDATE(A${r},1))`,
      nguoi(`,${A}>=A${r},${A}<EDATE(A${r},1)`)]);
  }
  s.getRange(1, 1, tom.length, 3).setValues(tom.map((r) => r.map((c) => (String(c).startsWith('=') ? '' : c))));
  tom.forEach((r, i) => r.forEach((c, j) => { if (String(c).startsWith('=')) s.getRange(i + 1, j + 1).setFormula(c); }));
  s.getRange(7, 1, 12, 1).setNumberFormat('mm/yyyy');
  s.getRange('E1').setFormula(
    `=QUERY(${L}B2:B,"select B, count(B) where B is not null group by B order by count(B) desc label B 'Phép phân tích', count(B) 'Số lượt'",0)`);
  [1, 6].forEach((row) => s.getRange(row, 1, 1, 3).setFontWeight('bold').setBackground('#e5ecf7'));
  s.getRange(1, 5, 1, 2).setFontWeight('bold').setBackground('#e5ecf7');
  s.setColumnWidth(1, 160);
  s.setColumnWidth(3, 170);
  s.setColumnWidth(5, 200);
}

function traVe_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
