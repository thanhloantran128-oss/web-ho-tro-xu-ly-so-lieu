"use strict";
/* Câu hỏi nghiên cứu & kế hoạch · kiểm tra chất lượng phiếu · trả lời theo câu hỏi.
   Dùng chung tiện ích và trạng thái S của app.js (nạp trước file này). */

// =====================================================================
// CÂU HỎI NGHIÊN CỨU & KẾ HOẠCH
// =====================================================================
const KH_KHOA = "ke-hoach-nghien-cuu";
const KIEU_BIEN = [["phan_loai", "Phân loại (nhóm)"], ["dinh_luong", "Số đo"], ["likert", "Thang Likert tự xây dựng"],
  ["thang_chuan", "Thang đo chuẩn"], ["nhieu_lua_chon", "Câu nhiều lựa chọn"]];
const DANG_CAU = [["mo_ta", "Mô tả thực trạng / tỷ lệ"], ["so_sanh", "So sánh giữa các nhóm"],
  ["lien_he", "Mối liên hệ giữa hai yếu tố"], ["truoc_sau", "Thay đổi trước – sau (cùng người đo hai lần)"]];
const VAI_TRO = {
  mo_ta: ["Biến cần mô tả", null],
  so_sanh: ["Chia nhóm theo (biến phân loại)", "So sánh về"],
  lien_he: ["Yếu tố thứ nhất", "Yếu tố thứ hai"],
  truoc_sau: ["Lần đo 1 (trước)", "Lần đo 2 (sau)"],
};

const newId = () => Math.random().toString(36).slice(2, 10);
const emptyPlan = () => ({ ten_de_tai: "", doi_tuong: "", bien: [{ id: newId(), ten: "", kieu: "phan_loai", nhom: "" }],
  cau_hoi: [{ id: newId(), dang: "", x: "", y: "", cau_hoi_rieng: "" }] });

/** 'Số giờ ngủ' → 'SoGioNgu' – giống research.ma_tu_ten ở máy chủ. */
function maTuTen(ten) {
  const s = String(ten || "").replace(/đ/g, "d").replace(/Đ/g, "D").normalize("NFD").replace(/[̀-ͯ]/g, "");
  let out = (s.match(/[A-Za-z0-9]+/g) || []).map((w) => w[0].toUpperCase() + w.slice(1)).join("");
  if (out && !/^[A-Za-z]/.test(out)) out = "B" + out;
  return out.slice(0, 30);
}
const maOf = (v) => (v.ma || "").trim() || maTuTen(v.ten);

function luuKeHoach() {
  try { localStorage.setItem(KH_KHOA, JSON.stringify(S.planInput)); } catch { /* bộ nhớ trình duyệt bị chặn: vẫn dùng được trong phiên */ }
}
function docKeHoach() {
  try { const v = JSON.parse(localStorage.getItem(KH_KHOA) || "null"); if (v && Array.isArray(v.bien)) return v; } catch { /* bỏ qua */ }
  return null;
}

/** Mô hình giao diện (biến có id cố định) → kế hoạch gửi máy chủ (biến gọi bằng mã cột). */
function toBackend(P = S.planInput) {
  const ma = Object.fromEntries(P.bien.map((v) => [v.id, maOf(v)]));
  const split = (s) => String(s || "").split(/[,;\n]+/).map((x) => x.trim()).filter(Boolean);
  return {
    ten_de_tai: P.ten_de_tai, doi_tuong: P.doi_tuong, muc_anh_huong: P.muc_anh_huong || "trung_binh", tong_the: P.tong_the || null,
    bien: P.bien.filter((v) => v.ten.trim()).map((v) => ({ ma: maOf(v), ten: v.ten, kieu: v.kieu, nhom: split(v.nhom),
      so_cau: v.so_cau, so_muc: v.so_muc, thang: v.thang, min: v.min, max: v.max })),
    cau_hoi: P.cau_hoi.map((q) => ({ dang: q.dang, x: ma[q.x] || "", y: ma[q.y] || "", cau_hoi_rieng: q.cau_hoi_rieng })),
  };
}
/** Kế hoạch đọc từ file mẫu (biến gọi bằng mã) → mô hình giao diện. */
function fromBackend(K) {
  const bien = (K.bien || []).map((b) => ({ ...b, id: newId(), nhom: (b.nhom || []).join(", ") }));
  const id = Object.fromEntries(bien.map((v) => [maOf(v), v.id]));
  return { ten_de_tai: K.ten_de_tai || "", doi_tuong: K.doi_tuong || "", muc_anh_huong: K.muc_anh_huong || "trung_binh", tong_the: K.tong_the || "", bien,
    cau_hoi: (K.cau_hoi || []).map((q) => ({ id: newId(), dang: q.dang || "", x: id[q.x] || "", y: id[q.y] || "", cau_hoi_rieng: q.cau_hoi_rieng || "" })) };
}

let khHen = null;
function henXayDung() { clearTimeout(khHen); khHen = setTimeout(xayDungKeHoach, 300); }
async function xayDungKeHoach() {
  luuKeHoach();
  try { S.plan = await api("/ke-hoach", { json: toBackend() }); } catch (err) { setMsg($("#ch-thong-bao"), err.message, "err"); return; }
  setMsg($("#ch-thong-bao"), "");
  veCauHoi();
  veKeHoach();
  if (S.preview) renderPlanPanel();
}

// ---------- Biến ----------
function veBien() {
  const box = $("#ch-bien");
  if (!box) return;
  box.replaceChildren(...S.planInput.bien.map((v) => {
    const change = (patch, redraw = false) => { Object.assign(v, patch); if (redraw) veBien(); henXayDung(); };
    const ma = h("input", { type: "text", value: v.ma || "", placeholder: maTuTen(v.ten) || "MaCot", "aria-label": "Mã cột",
      oninput: (e) => change({ ma: e.target.value.trim() }) });
    const ten = h("input", { type: "text", value: v.ten, placeholder: "Ví dụ: Số giờ ngủ", "aria-label": "Tên biến",
      oninput: (e) => { ma.placeholder = maTuTen(e.target.value) || "MaCot"; change({ ten: e.target.value }); } });
    const kieu = h("select", { "aria-label": "Loại biến", onchange: (e) => change({ kieu: e.target.value }, true) },
      KIEU_BIEN.map(([k, l]) => h("option", { value: k, selected: k === v.kieu }, l)));
    let extra = null;
    if (v.kieu === "phan_loai" || v.kieu === "nhieu_lua_chon") {
      extra = h("label", { class: "field" }, v.kieu === "phan_loai" ? "Các nhóm (cách nhau dấu phẩy)" : "Các lựa chọn (cách nhau dấu phẩy)",
        h("input", { type: "text", value: v.nhom || "", placeholder: v.kieu === "phan_loai" ? "Nam, Nữ" : "Facebook, TikTok, YouTube",
          oninput: (e) => change({ nhom: e.target.value }) }));
    } else if (v.kieu === "likert") {
      extra = h("div", { class: "minmax" },
        h("label", { class: "field" }, "Số câu", h("input", { type: "number", min: 1, value: v.so_cau || 4, oninput: (e) => change({ so_cau: Number(e.target.value) }) })),
        h("label", { class: "field" }, "Số mức", h("select", { onchange: (e) => change({ so_muc: Number(e.target.value) }) },
          [5, 7].map((n) => h("option", { value: n, selected: n === (v.so_muc || 5) }, `${n} mức`)))));
    } else if (v.kieu === "thang_chuan") {
      extra = h("label", { class: "field" }, "Thang đo", h("select", { onchange: (e) => change({ thang: e.target.value }) },
        h("option", { value: "" }, "— Chọn thang —"),
        S.library.map((s) => h("option", { value: s.ma, selected: s.ma === v.thang }, `${s.ma} – ${s.ten_viet}`))));
    } else if (v.kieu === "dinh_luong") {
      extra = h("div", { class: "minmax" },
        h("label", { class: "field" }, "Nhỏ nhất", h("input", { type: "number", value: v.min ?? "", oninput: (e) => change({ min: e.target.value === "" ? undefined : Number(e.target.value) }) })),
        h("label", { class: "field" }, "Lớn nhất", h("input", { type: "number", value: v.max ?? "", oninput: (e) => change({ max: e.target.value === "" ? undefined : Number(e.target.value) }) })));
    }
    return h("div", { class: "row-editor ch-row" },
      h("label", { class: "field" }, "Tên biến", ten), h("label", { class: "field" }, "Loại", kieu),
      h("div", { class: "ch-extra" }, extra), h("label", { class: "field" }, "Mã cột (tự tạo)", ma),
      h("button", { class: "btn small danger", type: "button", title: "Xóa biến", onclick: () => {
        S.planInput.bien = S.planInput.bien.filter((x) => x !== v);
        S.planInput.cau_hoi.forEach((q) => { if (q.x === v.id) q.x = ""; if (q.y === v.id) q.y = ""; });
        veBien(); veCauHoi(true); henXayDung();
      } }, "✕"));
  }));
}

// ---------- Câu hỏi ----------
let cauKy = "";
/** Vẽ lại khung câu hỏi khi danh sách biến đổi (tên, loại); phần kết quả của từng câu luôn cập nhật. */
function veCauHoi(force = false) {
  const box = $("#ch-cau-hoi");
  if (!box) return;
  const ky = JSON.stringify(S.planInput.bien.map((v) => [v.id, v.ten, v.kieu])) + S.planInput.cau_hoi.length;
  if (force || ky !== cauKy) {
    cauKy = ky;
    const vars = S.planInput.bien.filter((v) => v.ten.trim());
    const kieuTen = Object.fromEntries(KIEU_BIEN);
    box.replaceChildren(...S.planInput.cau_hoi.map((q, i) => {
      const pick = (key) => h("select", { onchange: (e) => { q[key] = e.target.value; henXayDung(); } },
        h("option", { value: "" }, "— Chọn biến —"),
        vars.map((v) => h("option", { value: v.id, selected: v.id === q[key] }, `${v.ten} (${kieuTen[v.kieu]})`)));
      const [lx, ly] = VAI_TRO[q.dang] || ["Biến thứ nhất", "Biến thứ hai"];
      const dang = h("select", { onchange: (e) => { q.dang = e.target.value; veCauHoi(true); henXayDung(); } },
        h("option", { value: "" }, "— Chọn dạng câu hỏi —"),
        DANG_CAU.map(([k, l]) => h("option", { value: k, selected: k === q.dang }, l)));
      const vi = S.plan?.dang_cau_hoi?.[q.dang]?.vi_du;
      return h("div", { class: "group-box ch-q" },
        h("div", { class: "ch-q-head" }, h("strong", {}, `Câu hỏi ${i + 1}`),
          h("button", { class: "btn small danger", type: "button", title: "Xóa câu hỏi", onclick: () => {
            S.planInput.cau_hoi.splice(i, 1); veCauHoi(true); henXayDung();
          } }, "✕")),
        h("label", { class: "field" }, "Dạng câu hỏi", dang),
        vi ? h("p", { class: "hint" }, "Ví dụ: ", vi) : null,
        q.dang ? h("div", { class: "ch-pick" }, h("label", { class: "field" }, lx, pick("x")), ly ? h("label", { class: "field" }, ly, pick("y")) : null) : null,
        q.dang ? h("label", { class: "field" }, "Câu hỏi theo cách viết của bạn (không bắt buộc)",
          h("input", { type: "text", value: q.cau_hoi_rieng || "", placeholder: "Để trống: dùng câu hỏi web gợi ý",
            oninput: (e) => { q.cau_hoi_rieng = e.target.value; henXayDung(); } })) : null,
        h("div", { class: "ch-out", "data-i": i }));
    }));
  }
  (S.plan?.cau_hoi || []).forEach((r, i) => { const out = $(`.ch-out[data-i="${i}"]`, box); if (out) out.replaceChildren(...ketQuaCau(r)); });
}

/** Căn cứ của một con số cỡ mẫu: cách tính, nguồn, đối chiếu với bảng của Cohen (1992). */
function canCu(cc) {
  return h("details", { class: "can-cu" }, h("summary", {}, "Căn cứ"),
    h("p", {}, cc.cach_tinh),
    h("p", {}, h("strong", {}, "Nguồn: "), cc.nguon.join("; "), "."),
    cc.doi_chieu ? h("p", {}, h("strong", {}, "Đối chiếu: "), cc.doi_chieu) : null);
}

function ketQuaCau(r) {
  if (!r.dang) return [];
  if (r.loi.length) return [h("div", { class: "note err" }, r.loi.map((s) => h("p", { html: md(s) })))];
  const gt = r.gia_thuyet || {};
  return [h("div", { class: "note ok ch-goi-y" },
    h("p", {}, h("strong", {}, "Câu hỏi: "), r.cau_hoi),
    gt.khong_can ? h("p", { class: "hint" }, gt.khong_can)
      : h("ul", { class: "hyp" }, h("li", {}, h("strong", {}, "H0: "), gt.h0), h("li", {}, h("strong", {}, "H1: "), gt.h1)),
    h("p", {}, h("strong", {}, "Phép phân tích: "), r.phep.ten),
    r.co_mau ? h("p", {}, h("strong", {}, "Cỡ mẫu: "), r.co_mau.mo_ta) : null,
    r.co_mau?.can_cu ? canCu(r.co_mau.can_cu) : null),
    r.canh_bao.length ? h("div", { class: "note warn" }, r.canh_bao.map((s) => h("p", { html: md(s) }))) : null].filter(Boolean);
}

// ---------- Kế hoạch ----------
function veKeHoach() {
  const box = $("#ch-ke-hoach");
  if (!box || !S.plan) return;
  const P = S.plan;
  const ok = P.cau_hoi.filter((q) => !q.loi.length && q.phep);
  const parts = [];
  if (P.loi_bien.length) parts.push(h("div", { class: "note err" }, h("strong", {}, "Cần sửa biến"), h("ul", {}, P.loi_bien.map((s) => h("li", {}, s)))));
  if (!ok.length) {
    parts.push(h("p", { class: "hint" }, "Kế hoạch sẽ hiện ở đây khi có ít nhất một câu hỏi hợp lệ."));
  } else {
    if (P.ten_de_tai) parts.push(h("p", {}, h("strong", {}, "Đề tài: "), P.ten_de_tai));
    parts.push(table(["CH", "Câu hỏi nghiên cứu", "Giả thuyết", "Phép phân tích", "Cỡ mẫu tối thiểu"],
      ok.map((q) => [q.so, q.cau_hoi,
        q.gia_thuyet?.khong_can ? "Không cần (câu hỏi mô tả)" : `H0: ${q.gia_thuyet.h0} H1: ${q.gia_thuyet.h1}`,
        q.phep.ten, q.co_mau ? `≈ ${q.co_mau.n} người${q.co_mau.moi_nhom ? ` (${q.co_mau.moi_nhom}/nhóm)` : ""}` : "—"]), { num: [0] }));
    if (P.co_mau_toi_thieu) parts.push(h("div", { class: "note ok" }, h("strong", {}, `Nên thu tối thiểu khoảng ${P.co_mau_toi_thieu.n} phiếu hợp lệ`),
      ` (theo câu hỏi ${P.co_mau_toi_thieu.cau}, câu cần nhiều người nhất). Nên thu dư 10–20% vì sẽ có phiếu bị loại.`));
    parts.push(h("p", { class: "hint" }, P.gia_dinh_co_mau), h("p", { class: "hint" }, P.ghi_chu_gia_thuyet));
    const cc = P.can_cu_co_mau;
    parts.push(h("details", { class: "note can-cu-chung" }, h("summary", {}, h("strong", {}, "Căn cứ khoa học của cỡ mẫu và tài liệu tham khảo")),
      h("ul", {}, cc.giai_thich.map((s) => h("li", { html: md(s) }))),
      h("p", {}, h("strong", {}, "Tài liệu tham khảo (APA 7)")),
      h("ol", { class: "refs" }, cc.tai_lieu.map((s) => h("li", { html: md(s) })))));
  }
  box.replaceChildren(...parts);
}

function moKeHoach() {
  S.planInput = docKeHoach() || emptyPlan();
  $("#ch-de-tai").value = S.planInput.ten_de_tai || "";
  $("#ch-doi-tuong").value = S.planInput.doi_tuong || "";
  $("#ch-muc").value = S.planInput.muc_anh_huong || "trung_binh";
  $("#ch-tong-the").value = S.planInput.tong_the || "";
  veBien();
  veCauHoi(true);
  xayDungKeHoach();
}

$("#ch-de-tai").addEventListener("input", (e) => { S.planInput.ten_de_tai = e.target.value; henXayDung(); });
$("#ch-doi-tuong").addEventListener("input", (e) => { S.planInput.doi_tuong = e.target.value; henXayDung(); });
$("#ch-muc").addEventListener("change", (e) => { S.planInput.muc_anh_huong = e.target.value; henXayDung(); });
$("#ch-tong-the").addEventListener("input", (e) => { S.planInput.tong_the = e.target.value ? Number(e.target.value) : ""; henXayDung(); });
$("#ch-them-bien").addEventListener("click", () => { S.planInput.bien.push({ id: newId(), ten: "", kieu: "phan_loai", nhom: "" }); veBien(); });
$("#ch-them-cau").addEventListener("click", () => { S.planInput.cau_hoi.push({ id: newId(), dang: "", x: "", y: "", cau_hoi_rieng: "" }); veCauHoi(true); henXayDung(); });
$("#ch-xoa").addEventListener("click", () => {
  if (!confirm("Xóa toàn bộ biến và câu hỏi nghiên cứu đang lưu trên trình duyệt này?")) return;
  try { localStorage.removeItem(KH_KHOA); } catch { /* bỏ qua */ }
  moKeHoach();
});
$("#ch-kiem-tra").addEventListener("click", (e) => busy(e.target, async () => {
  const box = $("#ch-ket-qua-kiem-tra");
  try {
    const r = await api("/cau-hoi/nhan-dang", { json: { text: $("#ch-tu-viet").value } });
    box.replaceChildren(
      r.dang ? h("p", {}, "Dạng câu hỏi: ", h("strong", {}, r.ten_dang), ". Hãy chọn dạng này ở mục 2 và chọn biến để có giả thuyết và phép phân tích.") : null,
      r.canh_bao.length ? h("div", { class: "note warn" }, h("ul", {}, r.canh_bao.map((s) => h("li", { html: md(s) }))))
        : h("div", { class: "note ok" }, "Không thấy lỗi thường gặp."));
  } catch (err) { box.replaceChildren(h("div", { class: "note err" }, err.message)); }
}));
$("#ch-tai-excel").addEventListener("click", (e) => busy(e.target, async () => {
  try {
    const blob = await api("/ke-hoach/excel", { json: toBackend() });
    const a = h("a", { href: URL.createObjectURL(blob), download: "ke-hoach-nghien-cuu.xlsx" });
    document.body.append(a); a.click(); a.remove();
    setMsg($("#ch-thong-bao"), "Đã tải kế hoạch.", "ok");
  } catch (err) { setMsg($("#ch-thong-bao"), err.message, "err"); }
}));

// ---------- Thiết kế phiếu theo kế hoạch ----------
$("#ch-sang-thiet-ke").addEventListener("click", () => {
  const cfg = S.plan?.thiet_ke_phieu;
  if (!cfg || !S.plan.bien.length) { setMsg($("#ch-thong-bao"), "Kế hoạch chưa có biến nào hợp lệ.", "err"); return; }
  if (S.plan.loi_bien.length) { setMsg($("#ch-thong-bao"), "Hãy sửa các biến còn lỗi trước.", "err"); return; }
  $("#tk-de-tai").value = cfg.ten_de_tai || "";
  $("#tk-cot-chung").replaceChildren();
  cfg.cot_chung.forEach((c) => addCommonRow(c));
  $("#tk-likert-bien").replaceChildren();
  $("#tk-co-likert").checked = !!cfg.likert;
  $("#tk-likert-box").classList.toggle("hidden", !cfg.likert);
  if (cfg.likert) { $("#tk-so-muc").value = String(cfg.likert.so_muc); cfg.likert.bien.forEach((b) => addLikertRow(b)); }
  const coThang = cfg.thang_do.length > 0;
  $(`input[name="tk-dac-thu"][value="${coThang ? "co" : "khong"}"]`).checked = true;
  $("#tk-thang-list").classList.toggle("hidden", !coThang);
  $$(".tk-thang").forEach((x) => { x.checked = cfg.thang_do.includes(x.value); });
  S.designPlan = cfg.ke_hoach;
  $("#tk-tu-ke-hoach").replaceChildren(h("div", { class: "note ok" }, h("strong", {}, "Phiếu đã được điền theo kế hoạch nghiên cứu. "),
    "Hãy bổ sung nội dung câu hỏi và kiểm tra các lựa chọn. File mẫu sẽ mang theo kế hoạch: khi tải lên ở bước phân tích, web tự hiện danh sách câu hỏi để trả lời.",
    " ", h("button", { class: "btn small ghost", type: "button", onclick: () => { S.designPlan = null; $("#tk-tu-ke-hoach").replaceChildren(); } }, "Không gắn kế hoạch")));
  openTab("thiet-ke");
});

// =====================================================================
// KIỂM TRA CHẤT LƯỢNG PHIẾU TRẢ LỜI (bước 1 của phân tích)
// =====================================================================
async function kiemTraChatLuong() {
  const box = $("#pt-chat-luong");
  if (!box || !S.file) return;
  box.replaceChildren(h("p", { class: "hint" }, "Đang kiểm tra chất lượng phiếu…"));
  const form = new FormData();
  form.append("file", S.file);
  form.append("params", JSON.stringify(S.attention ? { chu_y: S.attention } : {}));
  try { S.quality = await api("/chat-luong", { form }); } catch (err) { box.replaceChildren(h("div", { class: "note err" }, err.message)); return; }
  veChatLuong();
}

/** Số dòng các phiếu học sinh đã quyết định loại. */
function phieuBiLoai() {
  const out = new Set();
  (S.quality?.nhom || []).forEach((g) => { if (S.qualityPicked[g.ma]) g.dong.forEach((d) => out.add(d)); });
  return [...out].sort((a, b) => a - b);
}

function veChatLuong() {
  const Q = S.quality, box = $("#pt-chat-luong");
  if (!Q || !box) return;
  const flagged = Q.nhom.filter((g) => g.so_phieu > 0);
  const rows = (g) => (g.dong.length > 30 ? `${g.dong.slice(0, 30).join(", ")} … (còn ${g.so_phieu - 30} dòng)` : g.dong.join(", "));
  const loai = phieuBiLoai();
  const chiTiet = Q.nhom.filter((g) => S.qualityPicked[g.ma] && g.so_phieu).map((g) => `${g.so_phieu} phiếu ${g.ly_do_bao_cao}`).join("; ");
  const cau = loai.length ? plain(fill(Q.mau_bao_cao, { n: Q.n, k: loai.length, chi_tiet: chiTiet, con_lai: Q.n - loai.length })) : "";
  const cols = [{ value: "", label: "— Không có câu kiểm tra —" }, ...S.columns.map((c) => ({ value: c, label: c }))];
  const cot = select("cl-cot", cols);
  cot.value = S.attention?.cot || "";
  const dung = h("input", { type: "text", class: "cl-dung", value: S.attention?.dung || "", placeholder: "Đáp án đúng, ví dụ: Đồng ý hoặc 4" });
  box.replaceChildren(h("details", { open: true },
    h("summary", {}, "Kiểm tra chất lượng phiếu trả lời ",
      flagged.length ? h("span", { class: "badge" }, `${flagged.length} nhóm cần xem`) : h("span", { class: "badge ok" }, "ổn")),
    h("p", { class: "hint" }, Q.gioi_thieu),
    flagged.length ? flagged.map((g) => h("div", { class: "group-box" },
      h("label", { class: "check" }, h("input", { type: "checkbox", checked: !!S.qualityPicked[g.ma], onchange: (e) => {
        S.qualityPicked[g.ma] = e.target.checked; veChatLuong(); renderPlanPanel();
      } }), h("strong", {}, `Loại ${g.so_phieu} phiếu: ${g.ten}`)),
      h("p", { class: "hint" }, g.giai_thich),
      h("p", { class: "hint" }, `Dòng trong file: ${rows(g)}`)))
      : h("div", { class: "note ok" }, Q.khong_co),
    h("details", {}, h("summary", {}, "Câu kiểm tra sự chú ý (không bắt buộc)"),
      h("p", { class: "hint" }, Q.chu_y_huong_dan),
      h("div", { class: "ch-pick" }, field("Cột câu kiểm tra", cot), field("Đáp án đúng", dung)),
      h("div", { class: "actions" }, h("button", { class: "btn small", type: "button", onclick: (e) => busy(e.target, async () => {
        S.attention = cot.value ? { cot: cot.value, dung: dung.value.trim() } : null;
        if (!S.attention) delete S.qualityPicked.chu_y;
        await kiemTraChatLuong();
      }) }, "Kiểm tra lại"))),
    loai.length ? h("div", { class: "note ok" }, h("strong", {}, `Sẽ loại ${loai.length} phiếu, còn ${Q.n - loai.length} phiếu được phân tích. `),
      h("p", {}, "Câu viết vào phần Phương pháp: ", h("em", {}, cau), " ",
        h("button", { class: "btn small ghost", type: "button", onclick: async (e) => {
          try { await navigator.clipboard.writeText(cau); e.target.textContent = "Đã chép"; } catch { e.target.textContent = "Không chép được"; }
        } }, "Chép"))) : null));
}

// =====================================================================
// TRẢ LỜI THEO CÂU HỎI NGHIÊN CỨU (bước 3 của phân tích)
// =====================================================================
const lowerFirst = (s) => (s && s.length > 1 && s[1] === s[1].toLowerCase() ? s[0].toLowerCase() + s.slice(1) : s);

/** Cột (hoặc điểm thang đo ★) đoán là ứng với biến của kế hoạch. */
function doanCot(v) {
  const scores = scoreColumns();
  if (v.kieu === "thang_chuan") {
    const of = scores.filter((s) => S.scaleReqs.some((r) => r.ma === v.thang) && s.cot.startsWith(v.thang + "_"));
    return (of.find((s) => s.cot.endsWith("_TONG")) || of[0])?.cot || "";
  }
  if (v.kieu === "likert") return scores.find((s) => s.cot === scoreName(v.ma, true))?.cot || "";
  const f = fold(v.ma), ft = fold(v.ten).replace(/\s+/g, "");
  return S.columns.find((c) => fold(c) === f) || S.columns.find((c) => fold(c).replace(/\s+/g, "") === ft)
    || S.columns.find((c) => fold(c).startsWith(fold(v.ten))) || "";
}

function renderPlanPanel() {
  const box = $("#pt-theo-ke-hoach");
  if (!box) return;
  const P = S.plan;
  const qs = (P?.cau_hoi || []).filter((q) => !q.loi.length && q.phep);
  if (!S.preview || !qs.length) { box.replaceChildren(); return; }
  const used = new Set(qs.flatMap((q) => [q.x, q.y]).filter(Boolean));
  const vars = P.bien.filter((v) => used.has(v.ma));
  vars.forEach((v) => { if (!S.planMap[v.ma] || ![...S.columns, ...scoreColumns().map((s) => s.cot)].includes(S.planMap[v.ma])) S.planMap[v.ma] = doanCot(v); });
  const opts = [{ value: "", label: "— Chưa ghép —" }, ...scoreColumns().map((s) => ({ value: s.cot, label: `★ ${s.ten} [${s.cot}]` })),
    ...S.columns.map((c) => ({ value: c, label: `${c} (${TEN_LOAI[typeOf(c)]})` }))];
  const mapRows = vars.map((v) => {
    const sel = select("", opts, { "aria-label": `Cột ứng với ${v.ten}`, onchange: (e) => { S.planMap[v.ma] = e.target.value; renderPlanPanel(); } });
    sel.value = S.planMap[v.ma] || "";
    const hint = !S.planMap[v.ma] && (v.kieu === "likert" || v.kieu === "thang_chuan")
      ? h("span", { class: "hint" }, "Khai báo thang đo ở bước 2 để có điểm ★") : "";
    return [`${v.ten} (${v.ten_kieu})`, sel, hint];
  });
  const loai = phieuBiLoai();
  box.replaceChildren(h("div", { class: "suggest ke-hoach-pt" },
    h("strong", {}, "Trả lời câu hỏi nghiên cứu theo kế hoạch"),
    h("p", { class: "hint" }, "Ghép mỗi biến của kế hoạch với cột trong file (web đã đoán sẵn), rồi bấm “Trả lời” ở từng câu hỏi. "
      + "Web tự chọn đúng phép phân tích; kiểm tra điều kiện vẫn chạy như khi chọn thủ công.",
      loai.length ? ` Đang loại ${loai.length} phiếu theo bước 1.` : ""),
    table(["Biến trong kế hoạch", "Cột trong file", ""], mapRows, { copy: false }),
    h("div", { class: "kh-cau" }, qs.map((q) => {
      const thieu = [q.x, q.y].filter((m) => m && !S.planMap[m]);
      const st = S.answers[q.so];
      return h("div", { class: "kh-cau-row" },
        h("div", {}, h("strong", {}, `CH${q.so}. `), q.cau_hoi, h("br"), h("small", { class: "hint" }, q.phep.ten),
          st?.loi ? h("div", { class: "note err" }, st.loi) : null),
        h("button", { class: "btn small primary", type: "button", disabled: thieu.length > 0 || null,
          title: thieu.length ? "Hãy ghép đủ biến với cột trong file" : "", onclick: (e) => busy(e.target, () => traLoi(q)) },
        st && !st.loi ? "Chạy lại" : "Trả lời"));
    })),
    bangTraLoi(qs)));
}

/** Tham số /phan-tich cho một câu hỏi của kế hoạch. */
function thamSoCauHoi(q) {
  const v = Object.fromEntries(S.plan.bien.map((b) => [b.ma, b]));
  const cx = S.planMap[q.x], cy = S.planMap[q.y];
  const tx = v[q.x]?.ten, ty = v[q.y]?.ten;
  const m = q.phep.ma;
  let p;
  if (m === "tan-suat") p = { analysis: "tan-suat", variable: cx, type: descType(cx), label: tx, thu_tu: orderOf(cx) };
  else if (m === "mo-ta") p = { analysis: "mo-ta", variables: [{ name: cx, type: "scale" }] };
  else if (m === "trung-binh") { p = { analysis: "trung-binh", variables: [{ name: cx, label: tx }] }; if ([5, 7].includes(likertPoints(cx))) p.scale_points = likertPoints(cx); }
  else if (m === "thang-do") p = { analysis: "thang-do" };
  else if (m === "nhieu-lua-chon" || m === "nhieu-lua-chon-nhom") {
    const col = m === "nhieu-lua-chon" ? cx : cy, bv = v[m === "nhieu-lua-chon" ? q.x : q.y];
    const cfg = S.multiCfg.find((x) => x.cot === col);
    p = { analysis: "nhieu-lua-chon", dang: "van_ban", cot: col, cac_lua_chon: cfg ? cfg.cac_lua_chon : bv.nhom || [], label: bv.ten };
    if (m === "nhieu-lua-chon-nhom") Object.assign(p, { nhom: cx, nhom_label: tx });
  } else if (["t-test-doc-lap", "anova", "so-sanh-nhom"].includes(m)) {
    const k = colInfo(cx)?.so_gia_tri_khac ?? 0, nhom = v[q.x]?.nhom || [];
    if (k === 2 || (k > 2 && nhom.length === 2)) {
      p = { analysis: "t-test", type: "independent", dv: cy, dv_label: lowerFirst(ty), group: cx };
      if (k > 2) p.nhom = nhom;
    } else p = { analysis: "anova", dv: cy, dv_label: lowerFirst(ty), factor: cx, factor_label: lowerFirst(tx) };
  } else if (m === "bang-cheo") {
    p = { analysis: "bang-cheo", hang: cx, cot: cy, hang_label: tx, cot_label: ty, thu_tu_hang: orderOf(cx), thu_tu_cot: orderOf(cy) };
  } else if (m === "tuong-quan") {
    const thuBac = [cx, cy].some((c) => !isScore(c) && ["likert", "ordinal"].includes(typeOf(c)));
    p = { analysis: "tuong-quan", bien: [cx, cy], phuong_phap: thuBac ? "spearman" : "pearson", nhan: { [cx]: tx, [cy]: ty } };
  } else if (m === "t-test-cap") {
    p = { analysis: "t-test", type: "paired", dv: cx, dv2: cy, labels: [tx, ty] };
  }
  withCommon(p);
  if (p.analysis === "thang-do" && !S.scaleReqs.length) throw new Error("Chưa khai báo thang đo nào ở bước 2.");
  return p;
}

async function traLoi(q) {
  try {
    const params = thamSoCauHoi(q);
    $("#pt-loai").value = params.analysis;
    renderForm();
    await runAnalysis(params);
    const g = S.lastResult.giai_thich;
    S.answers[q.so] = { phep: TEN_PHAN_TICH[S.lastResult.analysis] || q.phep.ten, tom_tat: plain(g?.tom_tat?.[0] || ""), bao_cao: plain(g?.bao_cao || "") };
    renderPlanPanel();
    $("#pt-ket-qua").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    S.answers[q.so] = { loi: String(err.message).split(/\n\n+/)[0].replace(/\*\*/g, "") };
    renderPlanPanel();
  }
}

function bangTraLoi(qs) {
  const done = qs.filter((q) => S.answers[q.so] && !S.answers[q.so].loi);
  if (!done.length) return null;
  return h("div", {}, h("h3", {}, "Tổng hợp trả lời câu hỏi nghiên cứu"),
    h("p", { class: "hint" }, "Dùng cho chương Kết quả – Kết luận. Hãy đọc lại từng kết quả chi tiết trước khi chép."),
    table(["CH", "Câu hỏi nghiên cứu", "Phép phân tích", "Trả lời ngắn", "Kết quả (mẫu câu APA)"],
      done.map((q) => [q.so, q.cau_hoi, S.answers[q.so].phep, S.answers[q.so].tom_tat, S.answers[q.so].bao_cao || "—"]), { num: [0] }));
}
