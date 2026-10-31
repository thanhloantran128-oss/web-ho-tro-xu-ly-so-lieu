"use strict";
/* Giao diện xử lý số liệu – HTML/JS thuần, gọi API cùng máy chủ. */

// ---------- Tiện ích ----------
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "html") el.innerHTML = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "value") el.value = v;
    else if (k === "checked" || k === "selected" || k === "disabled") el[k] = !!v;
    else el.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
/** Chuyển **đậm** và *nghiêng* thành HTML (nội dung đã được escape trước). */
const md = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\*(.+?)\*/g, "<em>$1</em>");
const plain = (s) => String(s ?? "").replace(/\*\*(.+?)\*\*/g, "$1").replace(/\*(.+?)\*/g, "$1");

function fmt(x, nd = 2) {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  if (typeof x !== "number") return String(x);
  const v = Math.abs(x) < 0.5 * 10 ** -nd ? 0 : x;
  return v.toFixed(nd).replace("-", "−").replace(".", ",");
}
const fmtP = (p) => (p === null || p === undefined ? "—" : p < 0.001 ? "< ,001" : fmt(p, 3).replace(/^0/, ""));
const fmtInt = (x) => (x === null || x === undefined ? "—" : Number.isInteger(x) ? String(x) : fmt(x));

function table(headers, rows, opts = {}) {
  const numCols = new Set(opts.num || []);
  const tbl = h("table", {},
    h("thead", {}, h("tr", {}, headers.map((t, i) => h("th", { class: numCols.has(i) ? "num" : null }, t)))),
    h("tbody", {}, rows.map((r, ri) => h("tr", { class: opts.flag && opts.flag(ri) ? "flag" : null },
      r.map((c, i) => h("td", { class: numCols.has(i) ? "num" : null }, c instanceof Node ? c : String(c ?? "—")))))));
  const wrap = h("div", { class: "table-wrap" }, tbl);
  if (opts.copy === false) return wrap;
  const btn = h("button", { class: "btn small ghost", title: "Dán vào Word: bảng kẻ ngang kiểu APA. Dán vào Excel: tự tách cột.",
    onclick: () => copyTable(tbl, btn) }, "📋 Chép bảng");
  return h("div", { class: "table-block" }, h("div", { class: "table-tools" }, btn), wrap);
}

/** Chép bảng ở hai dạng: HTML (Word giữ khung kiểu APA, Times New Roman 12 pt) và văn bản tách tab (Excel tự tách cột). */
async function copyTable(tbl, btn) {
  let rows = [...tbl.rows].map((tr) => [...tr.cells].map((td) => (td.querySelector("select")
    ? td.querySelector("select").selectedOptions[0]?.textContent || "" : td.innerText).replace(/\s*\n\s*/g, " ").trim()));
  const keep = rows[0].map((_, j) => rows.some((r) => r[j]));  // bỏ cột chỉ có thanh biểu đồ
  rows = rows.map((r) => r.filter((_, j) => keep[j]));
  const tsv = rows.map((r) => r.join("\t")).join("\n");
  const line = "1px solid #000";
  const html = `<table style="border-collapse:collapse;font-family:'Times New Roman',serif;font-size:12pt">` + rows.map((r, ri) => {
    const head = ri === 0, last = ri === rows.length - 1, tag = head ? "th" : "td";
    const border = `border:none;${head ? `border-top:${line};border-bottom:${line};` : ""}${last ? `border-bottom:${line};` : ""}`;
    return "<tr>" + r.map((c, i) => `<${tag} style="${border}padding:2pt 8pt;text-align:${i === 0 ? "left" : "center"};`
      + `font-weight:${head ? "bold" : "normal"}">${esc(c)}</${tag}>`).join("") + "</tr>";
  }).join("") + "</table>";
  const done = (txt) => { btn.textContent = txt; setTimeout(() => { btn.textContent = "📋 Chép bảng"; }, 1600); };
  try {
    await navigator.clipboard.write([new ClipboardItem({
      "text/html": new Blob([html], { type: "text/html" }), "text/plain": new Blob([tsv], { type: "text/plain" }) })]);
    return done("✓ Đã chép");
  } catch { /* trình duyệt cũ hoặc trang http thường: dùng cách chép truyền thống */ }
  done(copyLegacy(html, tsv) ? "✓ Đã chép" : "Không chép được – hãy bôi đen bảng rồi Ctrl+C");
}

/** Chép bằng cách chọn một vùng tạm chứa bảng HTML (hoạt động cả khi không có Clipboard API). */
function copyLegacy(html, tsv) {
  const box = h("div", { contenteditable: "true", style: "position:fixed;left:-9999px;top:0", html });
  document.body.append(box);
  const range = document.createRange();
  range.selectNodeContents(box);
  const sel = window.getSelection();
  sel.removeAllRanges(); sel.addRange(range);
  const onCopy = (e) => { e.clipboardData.setData("text/html", html); e.clipboardData.setData("text/plain", tsv); e.preventDefault(); };
  document.addEventListener("copy", onCopy);
  let ok = false;
  try { ok = document.execCommand("copy"); } catch { ok = false; }
  document.removeEventListener("copy", onCopy);
  sel.removeAllRanges(); box.remove();
  return ok;
}

async function api(path, { json, form } = {}) {
  const init = json ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(json) }
    : form ? { method: "POST", body: form } : {};
  const res = await fetch(path, init);
  const type = res.headers.get("content-type") || "";
  if (!res.ok) {
    let msg = `Lỗi ${res.status}`;
    if (type.includes("json")) { const b = await res.json(); msg = typeof b.detail === "string" ? b.detail : JSON.stringify(b.detail); }
    throw new Error(msg);
  }
  return type.includes("json") ? res.json() : res.blob();
}

function setMsg(el, text, kind = "") { el.textContent = text; el.className = "msg " + kind; }
async function busy(btn, fn) {
  btn.disabled = true;
  try { return await fn(); } finally { btn.disabled = false; }
}

// ---------- Trạng thái ----------
const S = {
  library: [],        // menu thang đặc thù (GET /thang-do)
  coAI: false,
  rules: null,        // ràng buộc t-test/ANOVA (GET /rang-buoc)
  types: {},          // loại thang đo từng cột {cột: {loai, so_muc, thu_tu}} – khai báo ở bước 1
  file: null,
  preview: null,
  columns: [],
  recode: {},         // chỉ số gợi ý đổi chữ → true/false
  missingCodes: [],   // mã thiếu đã xác nhận
  scaleReqs: [],      // tham số thang_do gửi /phan-tich
  multiCfg: [],       // cấu hình câu nhiều lựa chọn đọc từ file mẫu
  lastResult: null,
  chat: [],
};

// ---------- Tab ----------
function openTab(name) {
  $$(".tab").forEach((t) => { const on = t.dataset.tab === name; t.classList.toggle("active", on); t.setAttribute("aria-selected", on); });
  $$(".tab-panel").forEach((p) => p.classList.toggle("hidden", p.id !== "tab-" + name));
}
$$(".tab").forEach((b) => b.addEventListener("click", () => openTab(b.dataset.tab)));

// =====================================================================
// TAB 3 · KIẾN THỨC THỐNG KÊ
// =====================================================================
const NHAN_MUC = [["la_gi", "Là gì"], ["vi_sao", "Vì sao cần"], ["cach_doc", "Cách đọc"], ["vi_du", "Ví dụ"], ["luu_y", "Lưu ý"]];
/** Bỏ dấu tiếng Việt để tìm kiếm không phân biệt dấu. */
const fold = (s) => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();

function renderKnowledge(K) {
  S.knowledge = K;
  $("#kt-gioi-thieu").innerHTML = `<p>${md(K.gioi_thieu)}</p>`;
  const B = K.bang_chon_phep;
  const content = [h("div", { class: "card", id: "kt-chon-phep" }, h("h2", {}, B.tieu_de), h("p", { class: "hint", html: md(B.ghi_chu) }),
    table(B.cot, B.hang.map((r) => r.map((c) => h("span", { html: md(c) })))))];
  const toc = [h("a", { href: "#kt-chon-phep", class: "ch" }, B.tieu_de)];
  for (const ch of K.chuong) {
    toc.push(h("a", { href: `#${ch.id}`, class: "ch" }, ch.ten));
    const items = ch.muc.map((m) => {
      toc.push(h("a", { href: `#kt-${m.id}`, "data-item": m.id }, m.ten));
      const text = fold([m.ten, m.ten_en, ...NHAN_MUC.map(([k]) => m[k])].join(" "));
      return h("details", { class: "kt-item", id: `kt-${m.id}`, "data-text": text },
        h("summary", {}, m.ten, m.ten_en ? h("small", {}, m.ten_en) : null),
        h("dl", {}, NHAN_MUC.filter(([k]) => m[k]).flatMap(([k, label]) => [h("dt", {}, label), h("dd", { html: md(m[k]) })])));
    });
    content.push(h("div", { class: "card kt-chuong", id: ch.id }, h("h2", {}, ch.ten), ch.gioi_thieu ? h("p", { class: "hint", html: md(ch.gioi_thieu) }) : null, ...items));
  }
  $("#kt-noi-dung").replaceChildren(...content);
  $("#kt-muc-luc").replaceChildren(...toc);
  $$("#kt-muc-luc a").forEach((a) => a.addEventListener("click", (e) => {
    e.preventDefault();
    const id = a.getAttribute("href").slice(1);
    const el = document.getElementById(id);
    if (el?.tagName === "DETAILS") el.open = true;
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
  }));
}

$("#kt-tim").addEventListener("input", (e) => {
  const q = fold(e.target.value.trim());
  let shown = 0;
  $$(".kt-item").forEach((d) => {
    const hit = !q || d.dataset.text.includes(q);
    d.classList.toggle("hidden", !hit);
    d.open = !!q && hit;
    if (hit) shown++;
  });
  $$(".kt-chuong").forEach((c) => c.classList.toggle("hidden", !!q && !$$(".kt-item:not(.hidden)", c).length));
  $("#kt-chon-phep").classList.toggle("hidden", !!q);
  $("#kt-dem").textContent = q ? `${shown} mục phù hợp` : "";
});

/** Mở tab kiến thức tại các mục liên quan (gọi từ màn hình kết quả). */
function gotoKnowledge(ids) {
  $("#kt-tim").value = ""; $("#kt-tim").dispatchEvent(new Event("input"));
  openTab("kien-thuc");
  ids.forEach((id) => { const d = document.getElementById(`kt-${id}`); if (d) { d.open = true; d.classList.add("flash"); setTimeout(() => d.classList.remove("flash"), 2500); } });
  document.getElementById(`kt-${ids[0]}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function knowledgeLinks(analysis) {
  const K = S.knowledge;
  const ids = (K?.lien_ket?.[analysis] || []).filter((id) => document.getElementById(`kt-${id}`));
  if (!ids.length) return null;
  const name = (id) => K.chuong.flatMap((c) => c.muc).find((m) => m.id === id)?.ten || id;
  return h("div", { class: "kt-links" }, h("span", { class: "hint" }, "📘 Tìm hiểu thêm:"),
    ids.map((id) => h("button", { class: "btn small ghost", onclick: () => gotoKnowledge([id]) }, name(id))));
}

// =====================================================================
// TAB 1 · THIẾT KẾ PHIẾU
// =====================================================================
const LOAI = [["nhom", "Nhóm (chọn một)"], ["so", "Số đo"], ["nhieu_lua_chon", "Nhiều lựa chọn"], ["chu", "Chữ tự do"]];

function addCommonRow(d = {}) {
  const row = h("div", { class: "row-editor" },
    h("label", { class: "field" }, "Tên cột", h("input", { type: "text", class: "c-ten", value: d.ten || "", placeholder: "GioiTinh" })),
    h("label", { class: "field" }, "Nội dung câu hỏi", h("input", { type: "text", class: "c-cau", value: d.cau_hoi || "" })),
    h("label", { class: "field" }, "Loại",
      h("select", { class: "c-loai", onchange: () => sync() }, LOAI.map(([v, t]) => h("option", { value: v, selected: v === (d.loai || "nhom") }, t)))),
    h("div", { class: "c-extra" },
      h("label", { class: "field c-opts" }, "Các lựa chọn (mỗi dòng một lựa chọn)",
        h("textarea", { class: "c-lua-chon", rows: 3 }, (d.lua_chon || []).join("\n"))),
      h("div", { class: "field c-range" }, "Khoảng giá trị",
        h("div", { class: "minmax" }, h("input", { type: "number", class: "c-min", placeholder: "min", value: d.min ?? "" }),
          h("input", { type: "number", class: "c-max", placeholder: "max", value: d.max ?? "" })))),
    h("button", { class: "btn small danger", title: "Xóa", onclick: () => row.remove() }, "✕"));
  function sync() {
    const t = $(".c-loai", row).value;
    $(".c-opts", row).classList.toggle("hidden", !(t === "nhom" || t === "nhieu_lua_chon"));
    $(".c-range", row).classList.toggle("hidden", t !== "so");
  }
  sync();
  $("#tk-cot-chung").append(row);
}

function addLikertRow(d = {}) {
  const row = h("div", { class: "row-editor likert" },
    h("label", { class: "field" }, "Mã biến", h("input", { type: "text", class: "l-ma", value: d.ma || "", placeholder: "HT" })),
    h("label", { class: "field" }, "Tên biến", h("input", { type: "text", class: "l-ten", value: d.ten || "", placeholder: "Hứng thú học tập" })),
    h("label", { class: "field" }, "Số câu", h("input", { type: "number", min: 1, class: "l-so-cau", value: d.so_cau || 4 })),
    h("label", { class: "field" }, "Câu đảo chiều (vd: 2, 4)", h("input", { type: "text", class: "l-dao", value: (d.dao || []).join(", ") })),
    h("button", { class: "btn small danger", title: "Xóa", onclick: () => row.remove() }, "✕"));
  $("#tk-likert-bien").append(row);
}

function renderScaleMenu() {
  const box = $("#tk-thang-list");
  box.replaceChildren(...S.library.map((s) => h("label", { class: "scale-item" },
    h("input", { type: "checkbox", value: s.ma, class: "tk-thang" }),
    h("span", {}, h("strong", {}, s.ma), s.nhay_cam ? h("span", { class: "badge" }, "nhạy cảm") : null,
      h("small", {}, s.ten_viet), h("small", {}, `${s.so_cau} câu · giá trị ${s.gia_tri.min}–${s.gia_tri.max}`)))));
}

$$('input[name="tk-dac-thu"]').forEach((r) => r.addEventListener("change", () =>
  $("#tk-thang-list").classList.toggle("hidden", $('input[name="tk-dac-thu"]:checked').value !== "co")));
$("#tk-co-likert").addEventListener("change", (e) => $("#tk-likert-box").classList.toggle("hidden", !e.target.checked));
$("#tk-them-cot").addEventListener("click", () => addCommonRow());
$("#tk-them-bien").addEventListener("click", () => addLikertRow());

function collectDesign() {
  const cfg = { ten_de_tai: $("#tk-de-tai").value.trim() || null, cot_chung: [], thang_do: [] };
  for (const row of $$("#tk-cot-chung .row-editor")) {
    const ten = $(".c-ten", row).value.trim();
    if (!ten) continue;
    const loai = $(".c-loai", row).value;
    const c = { ten, cau_hoi: $(".c-cau", row).value.trim(), loai };
    if (loai === "nhom" || loai === "nhieu_lua_chon") c.lua_chon = $(".c-lua-chon", row).value.split("\n").map((x) => x.trim()).filter(Boolean);
    if (loai === "so" && $(".c-min", row).value !== "" && $(".c-max", row).value !== "") {
      c.min = Number($(".c-min", row).value); c.max = Number($(".c-max", row).value);
    }
    cfg.cot_chung.push(c);
  }
  if ($("#tk-co-likert").checked) {
    const bien = $$("#tk-likert-bien .row-editor").map((row) => ({
      ma: $(".l-ma", row).value.trim(), ten: $(".l-ten", row).value.trim() || $(".l-ma", row).value.trim(),
      so_cau: Number($(".l-so-cau", row).value),
      dao: $(".l-dao", row).value.split(/[,;\s]+/).filter(Boolean).map(Number),
    })).filter((b) => b.ma);
    if (bien.length) cfg.likert = { so_muc: Number($("#tk-so-muc").value), bien };
  }
  if ($('input[name="tk-dac-thu"]:checked').value === "co") cfg.thang_do = $$(".tk-thang:checked").map((x) => x.value);
  return cfg;
}

$("#tk-tai-mau").addEventListener("click", (e) => busy(e.target, async () => {
  const msg = $("#tk-thong-bao");
  try {
    const cfg = collectDesign();
    if ($('input[name="tk-dac-thu"]:checked').value === "co" && !cfg.thang_do.length) throw new Error("Bạn chọn “Có” nhưng chưa đánh dấu thang đo nào.");
    const blob = await api("/mau-nhap-lieu", { json: cfg });
    const a = h("a", { href: URL.createObjectURL(blob), download: "mau-nhap-lieu.xlsx" });
    document.body.append(a); a.click(); a.remove();
    setMsg(msg, "Đã tải file mẫu. Nhập dữ liệu vào sheet “Dữ liệu”, rồi tải lên ở bước 2.", "ok");
  } catch (err) { setMsg(msg, err.message, "err"); }
}));

// =====================================================================
// TAB 2 · PHÂN TÍCH
// =====================================================================
$("#pt-file").addEventListener("change", async (e) => {
  const f = e.target.files[0];
  if (!f) return;
  Object.assign(S, { file: f, recode: {}, missingCodes: [], scaleReqs: [], multiCfg: [], types: {}, lastResult: null, chat: [] });
  $("#pt-file-label").textContent = f.name;
  $("#pt-ket-qua").replaceChildren();
  const box = $("#pt-xem-truoc");
  box.replaceChildren(h("p", { class: "hint" }, "Đang đọc file…"));
  try {
    const form = new FormData(); form.append("file", f);
    S.preview = await api("/xem-truoc", { form });
    S.columns = S.preview.cot.map((c) => c.name);
    initTypes();
    renderPreview();
    $("#pt-buoc-2").classList.remove("hidden");
    $("#pt-buoc-3").classList.remove("hidden");
    renderScaleStep();
    renderForm();
  } catch (err) {
    box.replaceChildren(h("div", { class: "note err" }, err.message));
  }
});

/** Danh sách cột dài (tên cột Google Forms) chỉ hiện cột đầu và cột cuối. */
function shortList(cols) {
  const cut = (c) => (c.length > 45 ? c.slice(0, 42) + "…" : c);
  return cols.length <= 3 ? cols.map(cut).join(", ") : `${cut(cols[0])} … ${cut(cols[cols.length - 1])}`;
}

function renderPreview() {
  const P = S.preview;
  const out = [h("p", {}, `Đã đọc ${P.n_dong} dòng (người trả lời) và ${P.cot.length} cột.`)];
  if (P.goi_y_ma_hoa_chu.length) {
    out.push(h("div", { class: "note warn" }, h("strong", {}, "Có cột Likert đang ở dạng chữ. "),
      "Cần đổi sang số trước khi tính. Hãy kiểm tra bảng đổi rồi đánh dấu để xác nhận:",
      ...P.goi_y_ma_hoa_chu.map((g, i) => h("div", { class: "group-box" },
        g.khop_hoan_toan
          ? h("label", { class: "check" }, h("input", { type: "checkbox", onchange: (e) => {
            S.recode[i] = e.target.checked;
            if (e.target.checked) setType(g.cot, { loai: "likert", so_muc: Object.keys(g.bang).length }); else renderForm();
          } }),
            `Đổi ${g.cot.length} cột (${shortList(g.cot)}) theo bộ nhãn “${g.ten}”`)
          : h("p", {}, `Cột ${g.cot.join(", ")} có nhãn chưa nhận ra: ${g.gia_tri_chua_khop.join(", ")}. Hãy sửa nhãn trong file cho khớp bộ “${g.ten}”.`),
        table(["Nhãn", "Điểm"], Object.entries(g.bang).map(([k, v]) => [k, v]), { num: [1] })))));
  }
  if (P.canh_bao_ma_thieu.length) {
    const codes = [...new Set(P.canh_bao_ma_thieu.flatMap((w) => w.gia_tri))];
    out.push(h("div", { class: "note warn" }, h("strong", {}, "Nghi có mã “không trả lời” kiểu SPSS. "),
      h("ul", {}, P.canh_bao_ma_thieu.map((w) => h("li", {}, `Cột ${w.cot}: ${w.so_o} ô mang giá trị ${w.gia_tri.join(", ")} (dòng ${w.dong.join(", ")})`))),
      h("label", { class: "check" }, h("input", { type: "checkbox", onchange: (e) => { S.missingCodes = e.target.checked ? codes : []; } }),
        `Đúng, chuyển các giá trị ${codes.join(", ")} thành ô trống`)));
  }
  out.push(h("div", { id: "ty-panel" }));
  $("#pt-xem-truoc").replaceChildren(...out);
  renderTypesPanel();
}

// ---------- Bước 2: thang đo ----------
function libraryScale(ma) { return S.library.find((s) => s.ma === ma); }

function renderScaleStep() {
  const box = $("#pt-thang-do");
  const P = S.preview;
  const cfg = P.cau_hinh_tu_file_mau;
  const parts = [];
  if (cfg && cfg.hop_le) {
    S.scaleReqs = cfg.thang_do.map(({ bang_ghep, ...req }) => req);
    S.multiCfg = cfg.nhieu_lua_chon || [];
    parts.push(h("div", { class: "note ok" }, h("strong", {}, "Đã nhận cấu hình từ file mẫu. "),
      S.scaleReqs.length ? "Thang đo và câu đảo chiều đã được khai báo sẵn; bạn chỉ cần soát lại bảng ghép bên dưới." : "File không dùng thang đo nào."));
    cfg.thang_do.forEach((req) => parts.push(mappingBox(req.ma === "LIKERT" ? "Thang Likert tự xây dựng" : `${req.ma} – ${libraryScale(req.ma)?.ten_viet || ""}`, req.bang_ghep)));
  } else {
    if (cfg && !cfg.hop_le) parts.push(h("div", { class: "note warn" }, cfg.thong_bao, " Cột bị thiếu: ", cfg.cot_bi_thieu.join(", ")));
    parts.push(h("p", { class: "hint" }, "Nếu nghiên cứu chỉ dùng Likert tự xây dựng, bạn bỏ qua phần thang đặc thù và khai báo biến Likert ở cuối. Nếu không có thang nào, chuyển thẳng sang bước 3."));
    const groups = P.goi_y_thang_do.filter((g) => g.thang_co_the.length);
    if (groups.length) parts.push(h("h3", {}, "Gợi ý thang đo đặc thù"));
    groups.forEach((g) => parts.push(suggestionBox(g)));
    parts.push(likertDeclareBox());
  }
  parts.push(h("h3", {}, "Thang đo sẽ được chấm điểm"), h("div", { id: "pt-ds-thang" }));
  box.replaceChildren(...parts);
  renderScaleList();
}

function mappingTable(rows, editable, cols, onChange) {
  return table(["Câu", "Cột", "Tiểu thang", "Đảo chiều", "Min–max", "n", "Tương quan biến–tổng", ""],
    rows.map((r, i) => [r.cau,
      editable ? h("select", { onchange: (e) => onChange(i, e.target.value) }, cols.map((c) => h("option", { value: c, selected: c === r.cot }, c))) : r.cot,
      r.tieu_thang || "—", r.dao_chieu ? "✔" : "", r.min === undefined || r.min === null ? "—" : `${fmtInt(r.min)}–${fmtInt(r.max)}`,
      r.n ?? "—", r.tuong_quan_bien_tong === null || r.tuong_quan_bien_tong === undefined ? "—" : fmt(r.tuong_quan_bien_tong),
      r.nghi_sai_vi_tri ? "Nghi đặt sai vị trí" : ""]),
    { num: [0, 5, 6], flag: (i) => rows[i].nghi_sai_vi_tri });
}

function mappingBox(title, rows) {
  const flagged = (rows || []).filter((r) => r.nghi_sai_vi_tri).length;
  return h("details", { open: flagged ? true : null }, h("summary", {}, `${title} – bảng ghép câu và cột`,
    flagged ? h("span", { class: "badge" }, `${flagged} câu cần soát`) : h("span", { class: "badge ok" }, "ổn")),
    flagged ? h("p", { class: "hint" }, "Câu tô đỏ vẫn tương quan âm dù đã đảo đúng: có thể cột bị đặt sai vị trí câu hoặc khai báo câu đảo chiều chưa đúng.") : null,
    mappingTable(rows || [], false));
}

function suggestionBox(g) {
  const holder = h("div");
  const sel = h("select", { onchange: draw },
    h("option", { value: "" }, "— Chọn thang (hoặc không phải thang đặc thù) —"),
    g.thang_co_the.map((c, i) => h("option", { value: i }, `${c.ma} – ${c.ten_viet}${c.khop_chinh_xac ? " (khớp chính xác)" : ""}${c.lech_ma_hoa ? ` · lệch ${c.lech_ma_hoa}` : ""}`)));
  let mapping = [...g.cot];
  function draw() {
    holder.replaceChildren();
    if (sel.value === "") return;
    const cand = g.thang_co_the[Number(sel.value)];
    const spec = libraryScale(cand.ma);
    const rev = new Set(spec.cau_dao_nguoc);
    const rows = cand.bang_ghep || mapping.map((c, i) => ({ cau: i + 1, cot: c, dao_chieu: rev.has(i + 1) }));
    const offset = h("input", { type: "checkbox" });
    holder.append(
      h("p", { class: "hint" }, "Soát thứ tự: câu thứ mấy của thang ứng với cột nào. Đổi cột ở ô chọn nếu thứ tự trên phiếu khác bản gốc."),
      mappingTable(rows.map((r, i) => ({ ...r, cot: mapping[i] })), true, S.columns, (i, v) => { mapping[i] = v; }),
      cand.lech_ma_hoa ? h("label", { class: "check" }, offset,
        `Dữ liệu đang lệch ${cand.lech_ma_hoa} đơn vị so với thang gốc (${spec.gia_tri.min}–${spec.gia_tri.max}). Xác nhận trừ ${cand.lech_ma_hoa} cho mọi câu.`) : null,
      h("button", { class: "btn small primary", onclick: () => {
        S.scaleReqs = S.scaleReqs.filter((r) => r.ma !== cand.ma);
        S.scaleReqs.push({ ma: cand.ma, cot: [...mapping], dich_chuyen: offset.checked ? cand.lech_ma_hoa : null });
        renderScaleList();
      } }, "Dùng thang này"));
  }
  return h("div", { class: "group-box" },
    h("h3", {}, `Nhóm cột “${g.tien_to}”`),
    h("p", { class: "hint" }, `${g.cot.length} cột · giá trị quan sát ${fmtInt(g.khoang_quan_sat[0])}–${fmtInt(g.khoang_quan_sat[1])}`),
    sel, holder);
}

function likertDeclareBox() {
  const vars = h("div");
  const points = h("select", {}, h("option", { value: 5 }, "5 mức"), h("option", { value: 7 }, "7 mức"));
  function addVar() {
    const pick = h("div", { class: "cols-pick" }, S.columns.map((c) => h("label", { class: "check" },
      h("input", { type: "checkbox", value: c, class: "lv-col" }), c)));
    const rev = h("input", { type: "text", class: "lv-dao", placeholder: "Tên cột đảo chiều, cách nhau dấu phẩy" });
    const row = h("div", { class: "group-box" },
      h("div", { class: "row-editor likert", style: "grid-template-columns:1fr 2fr auto;background:none;border:0;padding:0" },
        h("label", { class: "field" }, "Mã biến", h("input", { type: "text", class: "lv-ma", placeholder: "HT" })),
        h("label", { class: "field" }, "Tên biến", h("input", { type: "text", class: "lv-ten", placeholder: "Hứng thú học tập" })),
        h("button", { class: "btn small danger", onclick: () => row.remove() }, "✕")),
      h("p", { class: "hint" }, "Chọn các cột (câu) thuộc biến này:"), pick,
      h("label", { class: "field" }, "Câu đảo chiều", rev));
    vars.append(row);
  }
  const msg = h("span", { class: "msg" });
  return h("details", {}, h("summary", {}, "Khai báo biến Likert tự xây dựng"),
    h("label", { class: "field inline" }, "Số mức", points), vars,
    h("div", { class: "actions" },
      h("button", { class: "btn ghost small", onclick: addVar }, "+ Thêm biến"),
      h("button", { class: "btn small primary", onclick: () => {
        try {
          const bien = $$(".group-box", vars).map((row) => {
            const ma = $(".lv-ma", row).value.trim();
            const cot = $$(".lv-col:checked", row).map((x) => x.value);
            const dao = $(".lv-dao", row).value.split(/[,;]+/).map((x) => x.trim()).filter(Boolean);
            if (!ma || !cot.length) throw new Error("Mỗi biến cần mã và ít nhất một cột.");
            const sai = dao.filter((d) => !cot.includes(d));
            if (sai.length) throw new Error(`Cột đảo chiều ${sai.join(", ")} không thuộc biến ${ma}.`);
            return { ma, ten: $(".lv-ten", row).value.trim() || ma, cot, dao };
          });
          if (!bien.length) throw new Error("Chưa có biến nào.");
          S.scaleReqs = S.scaleReqs.filter((r) => r.ma !== "LIKERT");
          S.scaleReqs.push({ ma: "LIKERT", gia_tri: { min: 1, max: Number(points.value) }, bien });
          setMsg(msg, "Đã lưu.", "ok");
          renderScaleList();
        } catch (err) { setMsg(msg, err.message, "err"); }
      } }, "Lưu các biến Likert"), msg));
}

/** Cùng quy tắc với máy chủ (scales.score_column_name): trùng cột có sẵn trong file thì thêm hậu tố. */
const scoreName = (name, isLikert) => (S.columns.includes(name) ? name + (isLikert ? "_TB" : "_DIEM") : name);

function scoreColumns() {
  const out = [];
  for (const r of S.scaleReqs) {
    if (r.ma === "LIKERT") r.bien.forEach((b) => out.push({ cot: scoreName(b.ma, true), ten: `${b.ten} (Likert)`, nhan: b.ten }));
    else (libraryScale(r.ma)?.cot_diem || []).forEach((c) => out.push({ cot: scoreName(c.cot, false), ten: `${r.ma} – ${c.ten}`,
      nhan: c.ten === "Điểm tổng" ? `điểm ${r.ma}` : `${c.ten.toLowerCase()} (${r.ma})` }));
  }
  return out;
}

/** Tên hiển thị mặc định của một biến: điểm thang đo dùng tên biến thay cho mã cột. */
function labelFor(col) {
  const s = scoreColumns().find((x) => x.cot === col);
  if (!s) return undefined;
  return s.nhan.charAt(0).toLowerCase() + s.nhan.slice(1);
}

function renderScaleList() {
  const box = $("#pt-ds-thang");
  if (!box) return;
  box.replaceChildren(S.scaleReqs.length
    ? h("div", {}, S.scaleReqs.map((r) => h("span", { class: "pill" },
      r.ma === "LIKERT" ? `Likert tự xây dựng: ${r.bien.map((b) => b.ma).join(", ")}` : r.ma,
      r.dich_chuyen ? ` (trừ ${r.dich_chuyen})` : "", " ",
      h("button", { class: "btn small ghost", title: "Bỏ", onclick: () => { S.scaleReqs = S.scaleReqs.filter((x) => x !== r); renderScaleList(); renderForm(); } }, "✕"))))
    : h("p", { class: "hint" }, "Chưa có thang nào. Không sao nếu bạn chỉ cần thống kê mô tả, tần suất hay câu nhiều lựa chọn."));
  renderForm();
}

// ---------- Loại thang đo của từng câu hỏi (khai báo ở bước 1) ----------
const LOAI_THANG = [["nominal", "Định danh"], ["ordinal", "Thứ bậc"], ["likert", "Likert"], ["scale", "Định lượng"],
  ["multi", "Nhiều lựa chọn"], ["skip", "Bỏ qua"]];
const TEN_LOAI = Object.fromEntries(LOAI_THANG);
const MO_TA_LOAI = [
  ["Định danh", "nhóm không có thứ tự: giới tính, lớp, nền tảng MXH dùng nhiều nhất, câu có/không (0/1)."],
  ["Thứ bậc", "nhóm có thứ tự: khối lớp, học lực, mức thu nhập, “dưới 5 / 5–6,4 / …”. Cần sắp thứ tự từ thấp đến cao."],
  ["Likert", "một câu thang đồng ý / tần suất (Rất không đồng ý … Rất đồng ý). Chọn đúng số mức. Một câu Likert được xử lý như biến thứ bậc; trung bình của nhiều câu Likert (khai báo ở bước 2) mới là biến định lượng."],
  ["Định lượng", "số đo thật: điểm số, số giờ, tuổi, chiều cao."],
  ["Nhiều lựa chọn", "câu cho chọn nhiều đáp án (Google Forms nối bằng dấu phẩy)."],
  ["Bỏ qua", "không phân tích: dấu thời gian, câu trả lời tự do, cột ghi chú."],
];
const colInfo = (c) => S.preview?.cot.find((x) => x.name === c);
const typeOf = (c) => S.types[c]?.loai;
const isScore = (c) => scoreColumns().some((s) => s.cot === c);
function recodedColumns() {
  const out = new Set();
  (S.preview?.goi_y_ma_hoa_chu || []).forEach((g, i) => { if (S.recode[i]) g.cot.forEach((c) => out.add(c)); });
  return out;
}
/** Cột có giá trị số (sẵn số, hoặc đã xác nhận đổi chữ Likert sang số). */
const isNumeric = (c) => { const i = colInfo(c); return (i && i.min !== undefined) || recodedColumns().has(c); };

function initTypes() {
  S.types = {};
  for (const c of S.preview.cot) S.types[c.name] = { loai: c.loai_de_xuat || "nominal", so_muc: c.so_muc || 5, thu_tu: c.cac_gia_tri };
}

function setType(cols, patch) {
  cols.forEach((c) => Object.assign(S.types[c], patch));
  renderTypesPanel();
  renderForm();
}

function renderTypesPanel() {
  const box = $("#ty-panel");
  if (!box) return;
  const open = box.querySelector("details")?.open ?? true;
  const selected = new Set($$(".ty-chon:checked", box).map((x) => x.value));
  const counts = Object.fromEntries(LOAI_THANG.map(([v]) => [v, 0]));
  S.columns.forEach((c) => counts[typeOf(c)]++);
  const rows = S.columns.map((col) => {
    const info = colInfo(col), t = S.types[col];
    const range = info.min !== undefined ? `${fmtInt(info.min)}–${fmtInt(info.max)}`
      : info.cac_gia_tri ? info.cac_gia_tri.slice(0, 3).join(", ") + (info.cac_gia_tri.length > 3 ? "…" : "") : "chữ";
    const loai = h("select", { "aria-label": `Loại thang đo của ${col}`, onchange: (e) => setType([col], { loai: e.target.value }) },
      LOAI_THANG.map(([v, l]) => h("option", { value: v, selected: v === t.loai }, l)));
    const muc = t.loai === "likert" ? h("select", { "aria-label": "Số mức", onchange: (e) => setType([col], { so_muc: Number(e.target.value) }) },
      [3, 4, 5, 6, 7, 10].map((n) => h("option", { value: n, selected: n === t.so_muc }, `${n} mức`))) : null;
    const order = t.loai === "ordinal" && info.cac_gia_tri ? h("button", { class: "btn small ghost", onclick: () => editOrder(col) }, "Sắp thứ tự") : null;
    const goc = info.nguon_loai === "file_mau" ? h("span", { class: "badge ok" }, "từ file mẫu") : h("span", { class: "hint", title: info.ly_do_de_xuat || "" }, info.ly_do_de_xuat || "");
    return [h("input", { type: "checkbox", class: "ty-chon", value: col, checked: selected.has(col) }),
      h("span", { title: col }, col.length > 50 ? col.slice(0, 47) + "…" : col),
      `${info.so_gia_tri_khac} giá trị · ${range}`, h("span", { class: "ty-ctrl" }, loai, muc, order), goc];
  });
  const bulk = h("select", {}, LOAI_THANG.map(([v, l]) => h("option", { value: v }, l)));
  box.replaceChildren(h("details", { open },
    h("summary", {}, "Loại thang đo của các câu hỏi ",
      h("span", { class: "hint" }, LOAI_THANG.filter(([v]) => counts[v]).map(([v, l]) => `${l}: ${counts[v]}`).join(" · "))),
    h("p", { class: "hint" }, "Web đã đề xuất loại cho từng cột; hãy kiểm tra và sửa nếu chưa đúng. Mọi phép phân tích và cảnh báo phía sau dựa vào khai báo này."),
    h("details", { class: "ty-legend" }, h("summary", {}, "Các loại thang đo nghĩa là gì?"),
      h("ul", {}, MO_TA_LOAI.map(([k, v]) => h("li", {}, h("strong", {}, k), ": ", v)))),
    h("div", { class: "actions" }, h("span", { class: "hint" }, "Đặt loại cho các cột đã đánh dấu:"), bulk,
      h("button", { class: "btn small", onclick: () => {
        const cols = $$(".ty-chon:checked", box).map((x) => x.value);
        if (cols.length) setType(cols, { loai: bulk.value });
      } }, "Áp dụng"),
      h("button", { class: "btn small ghost", onclick: () => $$(".ty-chon", box).forEach((x) => { x.checked = !x.checked; }) }, "Đảo chọn")),
    table(["", "Cột", "Dữ liệu", "Loại thang đo", "Lý do đề xuất"], rows, { copy: false }),
    h("div", { id: "ty-order" })));
}

function editOrder(col) {
  const area = h("textarea", { rows: Math.min((S.types[col].thu_tu || []).length, 8) }, (S.types[col].thu_tu || []).join("\n"));
  $("#ty-order").replaceChildren(h("div", { class: "group-box" },
    h("strong", {}, `Thứ tự các nhóm của “${col}”`), h("p", { class: "hint" }, "Sắp từ THẤP đến CAO, mỗi dòng một nhóm (cần cho % tích lũy và bảng chéo)."), area,
    h("div", { class: "actions" }, h("button", { class: "btn small primary", onclick: () => {
      S.types[col].thu_tu = area.value.split("\n").map((x) => x.trim()).filter(Boolean);
      $("#ty-order").replaceChildren(h("span", { class: "msg ok" }, `Đã lưu thứ tự cho “${col}”.`));
    } }, "Lưu thứ tự"))));
  $("#ty-order").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/** Loại gửi lên máy chủ cho thống kê mô tả / tần suất (multi, skip không dùng ở đây). */
const descType = (c) => ({ nominal: "nominal", ordinal: "ordinal", likert: "likert", scale: "scale" }[typeOf(c)] || "nominal");

// ---------- Bước 3: chọn phép phân tích ----------
/** Biến dùng được như biến định lượng (t-test, ANOVA, tương quan, trung bình): điểm thang đo ★ và cột số không phải định danh. */
function varOptions({ numericOnly = false, includeScores = true } = {}) {
  const cols = S.columns.filter((c) => {
    const t = typeOf(c);
    if (t === "skip" || t === "multi") return false;
    return !numericOnly || (["scale", "likert", "ordinal"].includes(t) && isNumeric(c));
  });
  const opts = cols.map((c) => ({ value: c, label: `${c} (${TEN_LOAI[typeOf(c)]})` }));
  if (includeScores) scoreColumns().forEach((s) => opts.unshift({ value: s.cot, label: `★ ${s.ten} [${s.cot}]` }));
  return opts;
}
/** Biến phân loại dùng làm nhóm / bảng chéo / tần suất. */
const groupOptions = () => S.columns.filter((c) => !["skip", "multi"].includes(typeOf(c)))
  .map((c) => ({ value: c, label: `${c} (${TEN_LOAI[typeOf(c)]})` }));
const select = (cls, opts, extra = {}) => h("select", { class: cls, ...extra }, opts.map((o) => h("option", { value: o.value }, o.label)));
const field = (label, el) => h("label", { class: "field" }, label, el);

function renderForm() {
  const box = $("#pt-form");
  if (!S.preview) return;
  const t = $("#pt-loai").value;
  const groups = groupOptions();
  const parts = [];
  if (t === "mo-ta") {
    const cols = S.columns.filter((c) => !["skip", "multi"].includes(typeOf(c)));
    parts.push(h("p", { class: "hint" }, "Đánh dấu các biến cần mô tả. Loại thang đo lấy theo khai báo ở bước 1 (biến định lượng, Likert: trung bình, độ lệch chuẩn; biến phân loại: bảng tần số). Câu nhiều lựa chọn hãy dùng phép “Câu nhiều lựa chọn”."),
      h("div", { class: "cols-pick" }, cols.map((c) => h("label", { class: "check" },
        h("input", { type: "checkbox", class: "mt-col", value: c }), `${c} (${TEN_LOAI[typeOf(c)]})`))));
  } else if (t === "tan-suat") {
    parts.push(field("Biến", select("f-var", groups)),
      h("p", { class: "hint" }, "Loại thang đo và thứ tự nhóm lấy theo khai báo ở bước 1."),
      field("Tên hiển thị (không bắt buộc)", h("input", { type: "text", class: "f-label" })));
  } else if (t === "nhieu-lua-chon") {
    const multi = S.columns.filter((c) => typeOf(c) === "multi");
    const others = S.columns.filter((c) => typeOf(c) !== "multi" && typeOf(c) !== "skip");
    const fromCfg = (c) => S.multiCfg.find((m) => m.cot === c);
    const optsBox = h("textarea", { class: "f-opts", rows: 5, placeholder: "Mỗi dòng một lựa chọn đúng như trên phiếu" });
    const colSel = select("f-var", [...multi, ...others].map((c) => ({ value: c, label: `${c} (${TEN_LOAI[typeOf(c)]})` })),
      { onchange: () => { const m = fromCfg(colSel.value); optsBox.value = m ? m.cac_lua_chon.join("\n") : ""; } });
    const dang = select("f-dang", [{ value: "van_ban", label: "Một ô chứa các lựa chọn nối bằng dấu phẩy (Google Forms)" }, { value: "nhi_phan", label: "Mỗi lựa chọn một cột 0/1" }]);
    const bin = h("div", { class: "cols-pick hidden" }, S.columns.map((c) => h("label", { class: "check" }, h("input", { type: "checkbox", class: "f-bin", value: c }), c)));
    const textBox = h("div", {}, field("Cột chứa câu trả lời", colSel), field("Danh sách lựa chọn gốc của phiếu (nên khai báo)", optsBox));
    dang.addEventListener("change", () => { textBox.classList.toggle("hidden", dang.value !== "van_ban"); bin.classList.toggle("hidden", dang.value !== "nhi_phan"); });
    queueMicrotask(() => colSel.dispatchEvent(new Event("change")));
    parts.push(field("Dạng dữ liệu", dang), textBox, bin,
      field("Tên câu hỏi (không bắt buộc)", h("input", { type: "text", class: "f-label" })),
      field("So sánh theo nhóm (không bắt buộc)", select("f-group", [{ value: "", label: "— Không so sánh —" }, ...groups])));
  } else if (t === "trung-binh") {
    const points = select("f-points", [{ value: "", label: "Không phải Likert" }, { value: 5, label: "5 mức" }, { value: 7, label: "7 mức" }]);
    const pick = h("div", { class: "cols-pick" }, varOptions({ numericOnly: true }).map((o) => h("label", { class: "check" },
      h("input", { type: "checkbox", class: "f-mean", value: o.value, onchange: () => {
        // Tự chọn số mức theo khai báo Likert của các biến đã chọn
        const muc = new Set($$(".f-mean:checked").map((x) => likertPoints(x.value)).filter(Boolean));
        points.value = muc.size === 1 && [5, 7].includes([...muc][0]) ? String([...muc][0]) : "";
      } }), o.label)));
    parts.push(h("p", { class: "hint" }, "Chọn các biến cần tính trung bình – độ lệch chuẩn:"), pick,
      field("Thang Likert (để diễn giải mức)", points));
  } else if (t === "thang-do") {
    parts.push(h("p", { class: "hint" }, S.scaleReqs.length ? "Chấm điểm các thang đã khai báo ở bước 2 và kiểm tra độ tin cậy." : "Chưa khai báo thang nào ở bước 2."));
  } else if (t === "t-test") {
    const kind = select("f-kind", [{ value: "independent", label: "Hai nhóm người khác nhau (Independent)" }, { value: "one-sample", label: "So với một giá trị (One-sample)" }, { value: "paired", label: "Cùng người đo hai lần (Paired)" }]);
    const ind = h("div", {}, field("Biến nhóm (đúng 2 nhóm)", select("f-group", groups)),
      field("Chỉ so sánh 2 nhóm sau (không bắt buộc, cách nhau dấu phẩy)", h("input", { type: "text", class: "f-levels", placeholder: "Nam, Nữ" })));
    const one = h("div", { class: "hidden" }, field("Giá trị so sánh (vd: 3 = mức trung lập thang 5)", h("input", { type: "number", class: "f-test", value: 3, step: "any" })));
    const pair = h("div", { class: "hidden" }, field("Lần đo 2", select("f-dv2", varOptions({ numericOnly: true }))),
      field("Tên hai lần đo", h("input", { type: "text", class: "f-pair-labels", placeholder: "Trước, Sau" })));
    kind.addEventListener("change", () => { ind.classList.toggle("hidden", kind.value !== "independent"); one.classList.toggle("hidden", kind.value !== "one-sample"); pair.classList.toggle("hidden", kind.value !== "paired"); });
    parts.push(field("Loại so sánh", kind), field("Biến cần so sánh (biến phụ thuộc)", select("f-dv", varOptions({ numericOnly: true }))),
      field("Tên biến hiển thị (không bắt buộc)", h("input", { type: "text", class: "f-dv-label", placeholder: "vd: mức căng thẳng" })), ind, one, pair);
  } else if (t === "bang-cheo") {
    parts.push(field("Biến hàng (thường là biến nhóm, ví dụ giới tính)", select("f-row", groups)),
      field("Biến cột", select("f-col", groups)),
      field("Tên biến hàng hiển thị (không bắt buộc)", h("input", { type: "text", class: "f-row-label" })),
      field("Tên biến cột hiển thị (không bắt buộc)", h("input", { type: "text", class: "f-col-label" })));
  } else if (t === "tuong-quan") {
    parts.push(h("p", { class: "hint" }, "Chọn từ 2 biến định lượng trở lên (số đo, điểm thang đo ★):"),
      h("div", { class: "cols-pick" }, varOptions({ numericOnly: true }).map((o) => h("label", { class: "check" },
        h("input", { type: "checkbox", class: "f-corr", value: o.value }), o.label))),
      field("Phương pháp", select("f-method", [{ value: "pearson", label: "Pearson – biến định lượng, phân phối gần chuẩn" },
        { value: "spearman", label: "Spearman – biến thứ bậc, câu Likert đơn lẻ, phân phối lệch" }])));
  } else if (t === "anova") {
    parts.push(field("Biến cần so sánh (biến phụ thuộc)", select("f-dv", varOptions({ numericOnly: true }))),
      field("Tên biến hiển thị (không bắt buộc)", h("input", { type: "text", class: "f-dv-label" })),
      field("Biến nhóm (từ 3 nhóm)", select("f-group", groups)),
      field("Tên biến nhóm hiển thị (không bắt buộc)", h("input", { type: "text", class: "f-group-label", placeholder: "vd: khối lớp" })));
  }
  box.replaceChildren(...parts);
  if (t === "t-test" || t === "anova" || t === "bang-cheo" || t === "tuong-quan") {
    if (t === "t-test" || t === "anova") box.append(h("p", { class: "hint" }, "Biến phụ thuộc chỉ liệt kê biến số (định lượng, Likert, thứ bậc) và điểm thang đo (★). "
      + "Biến định danh như giới tính, lớp không dùng được để so sánh trung bình; hãy dùng Tần suất hoặc Bảng chéo."));
    box.append(h("div", { id: "pt-kiem-tra" }));
    $$("select, input", box).forEach((el) => el.addEventListener("change", precheck));
    precheck();
  } else {
    $("#pt-chay").disabled = false;
  }
}
$("#pt-loai").addEventListener("change", renderForm);

function likertPoints(col) {
  if (typeOf(col) === "likert") return S.types[col].so_muc;
  const req = S.scaleReqs.find((r) => r.ma === "LIKERT" && r.bien.some((b) => scoreName(b.ma, true) === col));
  return req ? req.gia_tri.max : null;
}

// ---------- Kiểm tra ràng buộc ngay khi chọn biến (máy chủ vẫn kiểm tra lại khi chạy) ----------
const fill = (tpl, v) => String(tpl).replace(/\{(\w+)\}/g, (m, k) => (k in v ? v[k] : m));
const rangeOf = (col) => {
  const info = colInfo(col), t = S.types[col];
  if (info.min !== undefined) return [fmtInt(info.min), fmtInt(info.max)];
  return t.loai === "likert" ? ["1", String(t.so_muc)] : ["?", "?"];
};

function dvIssues(col, errors, warns, tenPt) {
  if (!col || isScore(col)) return;  // điểm thang đo nhiều câu: biến định lượng
  const info = colInfo(col);
  if (!info) return;
  const R = S.rules, t = typeOf(col), k = info.so_gia_tri_khac;
  if (["nominal", "multi", "skip"].includes(t)) errors.push(fill(R.chan.khai_bao_khong_dinh_luong, { bien: col, loai: TEN_LOAI[t].toLowerCase() }));
  else if (!isNumeric(col)) errors.push(`Cột “${col}” đang ở dạng chữ. Hãy xác nhận đổi chữ sang số ở bước 1 trước khi tính trung bình.`);
  else if (k === 1) errors.push(fill(R.chan.bien_hang_so, { bien: col, gia_tri: fmtInt(info.min) }));
  else if (k === 2) errors.push(fill(R.chan.bien_nhi_phan, { bien: col, gia_tri: `${rangeOf(col)[0]} và ${rangeOf(col)[1]}` }));
  else if (t === "likert" || t === "ordinal") {
    const [mn, mx] = rangeOf(col);
    warns.push(fill(R.canh_bao.bien_thu_bac, { bien: col, k, min: mn, max: mx, ten_pt: tenPt, p_pt: "sẽ hiện sau khi phân tích" }));
  }
}

function groupIssues(col, analysis, errors, warns, levels) {
  const info = colInfo(col);
  if (!info) return;
  const R = S.rules, t = typeOf(col), k = info.so_gia_tri_khac;
  if (t === "scale") { errors.push(fill(R.chan.khai_bao_nhom_dinh_luong, { nhom: col })); return; }
  if (analysis === "anova") {
    if (k === 2) errors.push(`Biến nhóm “${col}” chỉ có 2 nhóm. ANOVA dùng cho **từ 3 nhóm trở lên**; với 2 nhóm hãy dùng Independent t-test.`);
    else if (k > R.nguong.so_nhom_toi_da_bien_nhom) warns.push(fill(R.canh_bao.qua_nhieu_nhom, { nhom: col, k }));
  } else if (k > 2 && !levels) {
    errors.push(`Biến nhóm “${col}” có ${k} nhóm. Independent t-test chỉ so sánh **đúng 2 nhóm**: hãy nhập 2 nhóm cần so sánh ở ô bên dưới, hoặc dùng ANOVA để so sánh cả ${k} nhóm.`);
  } else if (k < 2) errors.push(`Biến nhóm “${col}” chỉ có 1 nhóm nên không so sánh được.`);
}

function precheck() {
  const box = $("#pt-kiem-tra");
  if (!box || !S.rules) return;
  const t = $("#pt-loai").value;
  const errors = [], warns = [];
  const R = S.rules;
  if (t === "bang-cheo") {
    const a = val("f-row"), b = val("f-col");
    if (a && a === b) errors.push(fill(R.chan.bang_cheo_trung_cot, { bien: a }));
    else for (const col of [a, b]) {
      const info = colInfo(col);
      if (!info) continue;
      const k = info.so_gia_tri_khac;
      if (typeOf(col) === "scale") errors.push(fill(R.chan.bang_cheo_so_do, { bien: col, k }));
      else if (k > R.nguong.so_nhom_toi_da_bien_nhom) warns.push(fill(R.canh_bao.bang_cheo_nhieu_nhom, { bien: col, k }));
    }
  } else if (t === "tuong-quan") {
    const cols = $$(".f-corr:checked").map((x) => x.value);
    const pearson = val("f-method") === "pearson";
    if (cols.length < 2) errors.push(R.chan.tuong_quan_it_bien);
    for (const col of cols) {
      if (isScore(col)) continue;
      const info = colInfo(col);
      if (!info) continue;
      const k = info.so_gia_tri_khac, ty = typeOf(col);
      if (["nominal", "multi", "skip"].includes(ty)) errors.push(fill(R.chan.tuong_quan_chu, { bien: col }));
      else if (k === 2) warns.push(fill(R.canh_bao.tuong_quan_nhi_phan, { bien: col }));
      else if (pearson && (ty === "likert" || ty === "ordinal")) {
        const [mn, mx] = rangeOf(col);
        warns.push(fill(R.canh_bao.tuong_quan_thu_bac, { bien: col, k, min: mn, max: mx }));
      }
    }
  } else if (t === "anova") {
    const dv = val("f-dv"), g = val("f-group");
    if (dv && dv === g) errors.push(fill(R.chan.trung_cot, { bien: dv }));
    else { dvIssues(dv, errors, warns, "Kruskal-Wallis"); groupIssues(g, "anova", errors, warns); }
  } else {
    const kind = val("f-kind"), dv = val("f-dv");
    if (kind === "independent") {
      const g = val("f-group");
      if (dv && dv === g) errors.push(fill(R.chan.trung_cot, { bien: dv }));
      else { dvIssues(dv, errors, warns, "Mann-Whitney U"); groupIssues(g, "t-test", errors, warns, val("f-levels")); }
    } else if (kind === "paired") {
      const dv2 = val("f-dv2");
      if (dv === dv2) errors.push(fill(R.chan.paired_trung_cot, { bien: dv }));
      else { dvIssues(dv, errors, warns, "Wilcoxon"); dvIssues(dv2, errors, warns, "Wilcoxon"); }
    } else dvIssues(dv, errors, warns, "Wilcoxon");
  }
  const list = (arr) => h("ul", {}, [...new Set(arr)].map((s) => h("li", { html: md(s) })));
  box.replaceChildren(...[
    errors.length ? h("div", { class: "note err" }, h("strong", {}, "Chưa chạy được phép này với các biến đã chọn"), list(errors)) : null,
    warns.length ? h("div", { class: "note warn" }, h("strong", {}, "Lưu ý trước khi chạy"), list(warns)) : null].filter(Boolean));
  $("#pt-chay").disabled = errors.length > 0;
}

function showError(el, text) {
  el.className = "msg";
  el.replaceChildren(h("div", { class: "note err" }, String(text).split(/\n\n+/).map((p) => h("p", { html: md(p) }))));
}

function val(cls) { const el = $("." + cls, $("#pt-form")); return el ? el.value.trim() : ""; }
const orderOf = (col) => (typeOf(col) === "ordinal" ? S.types[col]?.thu_tu : undefined);

function collectParams() {
  const t = $("#pt-loai").value;
  const p = { analysis: t };
  if (t === "mo-ta") {
    p.variables = $$(".mt-col:checked").map((x) => ({ name: x.value, type: descType(x.value), thu_tu: orderOf(x.value) }));
    if (!p.variables.length) throw new Error("Hãy chọn ít nhất một biến.");
  } else if (t === "tan-suat") {
    const v = val("f-var");
    Object.assign(p, { variable: v, type: descType(v), label: val("f-label") || undefined, thu_tu: orderOf(v) });
  } else if (t === "nhieu-lua-chon") {
    p.dang = val("f-dang");
    p.label = val("f-label") || undefined;
    if (p.dang === "van_ban") {
      p.cot = val("f-var");
      p.cac_lua_chon = $(".f-opts").value.split("\n").map((x) => x.trim()).filter(Boolean);
    } else {
      p.cot_lua_chon = $$(".f-bin:checked").map((x) => ({ cot: x.value, label: x.value }));
      if (!p.cot_lua_chon.length) throw new Error("Hãy chọn các cột 0/1.");
    }
    if (val("f-group")) { p.nhom = val("f-group"); p.nhom_label = val("f-group"); }
  } else if (t === "trung-binh") {
    p.variables = $$(".f-mean:checked").map((x) => ({ name: x.value, label: labelFor(x.value) && scoreColumns().find((s) => s.cot === x.value).nhan }));
    if (!p.variables.length) throw new Error("Hãy chọn ít nhất một biến.");
    if (val("f-points")) p.scale_points = Number(val("f-points"));
  } else if (t === "t-test") {
    p.type = val("f-kind"); p.dv = val("f-dv"); p.dv_label = val("f-dv-label") || labelFor(p.dv);
    if (p.type === "independent") {
      p.group = val("f-group");
      const lv = val("f-levels").split(",").map((x) => x.trim()).filter(Boolean);
      if (lv.length) { if (lv.length !== 2) throw new Error("Hãy nhập đúng 2 nhóm."); p.nhom = lv; }
    } else if (p.type === "one-sample") p.test_value = Number(val("f-test"));
    else { p.dv2 = val("f-dv2"); const l = val("f-pair-labels").split(",").map((x) => x.trim()).filter(Boolean); if (l.length === 2) p.labels = l; }
  } else if (t === "bang-cheo") {
    Object.assign(p, { hang: val("f-row"), cot: val("f-col"), hang_label: val("f-row-label") || undefined,
      cot_label: val("f-col-label") || undefined, thu_tu_hang: orderOf(val("f-row")), thu_tu_cot: orderOf(val("f-col")) });
  } else if (t === "tuong-quan") {
    p.bien = $$(".f-corr:checked").map((x) => x.value);
    p.phuong_phap = val("f-method");
    p.nhan = Object.fromEntries(p.bien.map((c) => [c, scoreColumns().find((s) => s.cot === c)?.nhan || c]));
  } else if (t === "anova") {
    Object.assign(p, { dv: val("f-dv"), dv_label: val("f-dv-label") || labelFor(val("f-dv")), factor: val("f-group"), factor_label: val("f-group-label") || undefined });
  }
  p.thang_do = S.scaleReqs;
  p.kieu_bien = Object.fromEntries(Object.entries(S.types).map(([c, v]) => [c, { loai: v.loai, so_muc: v.so_muc }]));
  const rc = (S.preview.goi_y_ma_hoa_chu || []).filter((g, i) => S.recode[i]).map((g) => ({ cot: g.cot, bo: g.bo }));
  if (rc.length) p.ma_hoa_chu = rc;
  if (S.missingCodes.length) p.ma_thieu = S.missingCodes;
  if (t === "thang-do" && !S.scaleReqs.length) throw new Error("Chưa khai báo thang đo nào ở bước 2.");
  return p;
}

async function runAnalysis(params) {
  const form = new FormData();
  form.append("file", S.file);
  form.append("params", JSON.stringify(params));
  const r = await api("/phan-tich", { form });
  S.lastResult = r; S.chat = [];
  renderResult(r);
}

$("#pt-chay").addEventListener("click", (e) => busy(e.target, async () => {
  const msg = $("#pt-thong-bao");
  try {
    setMsg(msg, "Đang tính…");
    await runAnalysis(collectParams());
    setMsg(msg, "");
    $("#pt-ket-qua").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) { showError(msg, err.message); }
}));

// ---------- Kết quả ----------
const TEN_PHAN_TICH = { "mo-ta": "Thống kê mô tả", "tan-suat": "Tần suất", "trung-binh": "Trung bình – độ lệch chuẩn",
  "t-test": "Kiểm định t", anova: "One-way ANOVA", "nhieu-lua-chon": "Câu nhiều lựa chọn", "thang-do": "Chấm điểm thang đo",
  "bang-cheo": "Bảng chéo – Chi-square", "tuong-quan": "Tương quan" };

function renderExplanation(g) {
  if (!g) return h("div", { class: "note warn" }, "Chưa tạo được lời giải thích tự động cho kết quả này.");
  const report = plain(g.bao_cao);
  const copyBtn = h("button", { class: "btn small", onclick: async () => {
    try { await navigator.clipboard.writeText(report); copyBtn.textContent = "Đã chép"; } catch { copyBtn.textContent = "Không chép được"; }
    setTimeout(() => { copyBtn.textContent = "Chép mẫu câu"; }, 1500);
  } }, "Chép mẫu câu");
  return h("div", {},
    h("div", { class: "summary" }, g.tom_tat.map((s) => h("p", { html: md(s) }))),
    g.canh_bao.length ? h("div", { class: "note warn" }, h("strong", {}, "Lưu ý"), h("ul", {}, g.canh_bao.map((s) => h("li", { html: md(s) })))) : null,
    h("details", {}, h("summary", {}, "Xem giải thích chi tiết"),
      g.chi_tiet.map((sec) => h("div", {}, h("h3", {}, sec.tieu_de), h("ul", {}, sec.noi_dung.map((s) => h("li", { html: md(s) })))))),
    g.bao_cao ? h("div", {}, h("h3", {}, "Mẫu câu viết báo cáo (APA)"), h("blockquote", { html: md(g.bao_cao) }), copyBtn) : null,
    g.goi_mo.length ? h("div", {}, h("h3", {}, "Câu hỏi gợi mở"), h("ul", {}, g.goi_mo.map((s) => h("li", { html: md(s) })))) : null,
    g.thuat_ngu.length ? h("details", {}, h("summary", {}, "Thuật ngữ"), h("ul", {}, g.thuat_ngu.map((s) => h("li", { html: md(s) })))) : null);
}

function barCell(pct) { return h("div", { class: "bar", style: `width:${Math.max(0, Math.min(100, pct || 0))}%` }); }

/** Bảng tần số kiểu SPSS; cột % tích lũy chỉ hiện với biến có thứ tự. */
function freqTable(rows, type) {
  const ordered = type === "ordinal" || type === "likert";
  const headers = ["Giá trị", "Tần số", "Percent", "Valid Percent", ...(ordered ? ["Cumulative Percent"] : []), ""];
  const total = rows.reduce((s, x) => s + x.freq, 0);
  const body = rows.map((x) => [x.label, x.freq, fmt(x.percent, 1), fmt(x.valid_percent, 1),
    ...(ordered ? [fmt(x.cum_percent, 1)] : []), barCell(x.valid_percent)]);
  body.push([h("strong", {}, "Tổng"), h("strong", {}, String(total)), "", h("strong", {}, "100,0"), ...(ordered ? [""] : []), ""]);
  return table(headers, body, { num: ordered ? [1, 2, 3, 4] : [1, 2, 3] });
}

function renderTables(r) {
  const t = r.analysis;
  if (t === "mo-ta") {
    // Biến định lượng: bảng M, SD…; biến định danh / thứ bậc / Likert: bảng tần số riêng cho từng biến
    const TEN_LOAI = { scale: "số đo", likert: "Likert", ordinal: "thứ bậc", nominal: "định danh" };
    const numVars = r.variables.filter((v) => v.type === "scale" || v.type === "likert");
    const catVars = r.variables.filter((v) => v.tan_suat && v.tan_suat.length);
    const parts = [];
    if (numVars.length) {
      parts.push(h("h3", {}, "Biến định lượng"), table(["Biến", "Loại", "n", "Thiếu", "M", "SD", "Mdn", "Min", "Max", "Skewness"],
        numVars.map((v) => [v.label, TEN_LOAI[v.type], v.n_valid, v.n_missing, fmt(v.mean), fmt(v.sd), fmtInt(v.median), fmtInt(v.min), fmtInt(v.max), fmt(v.skewness)]),
        { num: [2, 3, 4, 5, 6, 7, 8, 9] }));
    }
    if (catVars.length) {
      parts.push(h("h3", {}, "Phân bố tần số"));
      catVars.forEach((v) => parts.push(
        h("p", {}, h("strong", {}, v.label), ` · ${TEN_LOAI[v.type]} · n hợp lệ = ${v.n_valid}${v.n_missing ? ` · thiếu ${v.n_missing}` : ""}`),
        freqTable(v.tan_suat, v.type)));
    }
    return h("div", {}, ...parts);
  }
  if (t === "tan-suat") return freqTable(r.table, r.type);
  if (t === "nhieu-lua-chon") {
    const parts = [table(["Lựa chọn", "Số người chọn", "% số người", "% lượt chọn", ""],
      r.table.map((x) => [x.label, x.freq, fmt(x.pct_nguoi, 1), fmt(x.pct_luot, 1), barCell(x.pct_nguoi)]), { num: [1, 2, 3] })];
    if (r.so_sanh_nhom) {
      const names = r.so_sanh_nhom.cac_nhom.map((g) => `${g.label} (n=${g.n})`);
      parts.push(h("h3", {}, `So sánh theo ${r.so_sanh_nhom.nhom}`), table(["Lựa chọn", ...names, "Kiểm định", "χ²", "p", "p Bonferroni", "Cramér's V"],
        r.so_sanh_nhom.theo_lua_chon.map((x) => [x.label, ...x.pct_theo_nhom.map((v) => fmt(v, 1) + "%"), x.kiem_dinh || "—", fmt(x.chi2), fmtP(x.p), fmtP(x.p_bonferroni), fmt(x.cramers_v)])));
    }
    return h("div", {}, ...parts);
  }
  if (t === "trung-binh") {
    const rows = r.variables.map((v) => [v.label, v.n, fmt(v.mean), fmt(v.sd), fmtInt(v.median), fmtInt(v.min), fmtInt(v.max)]);
    if (r.composite) rows.push([`${r.composite.label || r.composite.name} (tổng hợp)`, r.composite.n, fmt(r.composite.mean), fmt(r.composite.sd), "—", "—", "—"]);
    return table(["Biến", "n", "M", "SD", "Mdn", "Min", "Max"], rows, { num: [1, 2, 3, 4, 5, 6] });
  }
  if (t === "t-test") {
    const parts = [table(["Nhóm / lần đo", "n", "M", "SD"], r.groups.map((g) => [g.label, g.n, fmt(g.mean), fmt(g.sd)]), { num: [1, 2, 3] })];
    const rows = [];
    if (r.levene) rows.push(["Levene's test", `F = ${fmt(r.levene.F)}`, "", fmtP(r.levene.p), "", ""]);
    const add = (name, s, mark) => rows.push([name + (mark ? " ← đọc dòng này" : ""), fmt(s.t), fmtInt(s.df % 1 ? Number(s.df.toFixed(2)) : s.df), fmtP(s.p), fmt(s.mean_diff), `[${fmt(s.ci95[0])}; ${fmt(s.ci95[1])}]`]);
    add(r.welch ? "Student (Equal variances assumed)" : "t-test", r.student, r.dong_nen_doc === "student");
    if (r.welch) add("Welch (Equal variances not assumed)", r.welch, r.dong_nen_doc === "welch");
    parts.push(table(["", "t", "df", "p", "Chênh lệch", "95% CI"], rows, { num: [1, 2, 3, 4] }),
      h("p", { class: "hint" }, `Cohen's d = ${fmt(r.cohens_d)}`, r.nonparametric ? ` · ${r.nonparametric.test}: p = ${fmtP(r.nonparametric.p)}` : ""));
    return h("div", {}, ...parts);
  }
  if (t === "anova") {
    const main = r.kiem_dinh_nen_doc;
    return h("div", {},
      table(["Nhóm", "n", "M", "SD"], r.groups.map((g) => [g.label, g.n, fmt(g.mean), fmt(g.sd)]), { num: [1, 2, 3] }),
      table(["Kiểm định", "F", "df1", "df2", "p", ""], [
        ["Levene's test", fmt(r.levene.F), r.levene.df1, r.levene.df2, fmtP(r.levene.p), ""],
        ["ANOVA", fmt(r.anova.F), r.anova.df1, r.anova.df2, fmtP(r.anova.p), main === "anova" ? "← đọc dòng này" : ""],
        ["Welch", fmt(r.welch.F), r.welch.df1, fmt(r.welch.df2), fmtP(r.welch.p), main === "welch" ? "← đọc dòng này" : ""],
      ], { num: [1, 2, 3, 4] }),
      h("p", { class: "hint" }, `η² = ${fmt(r.anova.eta_sq, 3)} · Kruskal-Wallis: p = ${fmtP(r.nonparametric.p)}`),
      r.co_y_nghia_tong_the ? h("div", {}, h("h3", {}, `Kiểm định sau: ${r.posthoc.method}`),
        table(["Nhóm I", "Nhóm J", "Chênh lệch (I − J)", "p"], r.posthoc.pairs.map((x) => [x.i, x.j, fmt(x.mean_diff), fmtP(x.p) + (x.p !== null && x.p <= 0.05 ? " *" : "")]), { num: [2, 3] })) : null);
  }
  if (t === "bang-cheo") {
    const R = r.hang.nhom, C = r.cot.nhom;
    const cell = (i, j) => h("span", {}, String(r.tan_so[i][j]), h("br"), h("small", { class: "hint" }, `${fmt(r.pct_hang[i][j], 1)}%`));
    const body = R.map((rn, i) => [rn, ...C.map((_, j) => cell(i, j)), h("strong", {}, String(r.tong_hang[i]))]);
    body.push([h("strong", {}, "Tổng"), ...r.tong_cot.map((x) => h("strong", {}, String(x))), h("strong", {}, String(r.n))]);
    const nums = C.map((_, j) => j + 1).concat([C.length + 1]);
    const lt5 = r.ky_vong.flat().filter((e) => e < 5).length;
    return h("div", {},
      h("p", { class: "hint" }, `Hàng: ${r.hang.label} · Cột: ${r.cot.label}. Mỗi ô: số người và % theo hàng.`),
      table([`${r.hang.label} \\ ${r.cot.label}`, ...C, "Tổng"], body, { num: nums }),
      table(["Kiểm định", "Giá trị", "df", "p"], [
        ["Pearson Chi-square" + (r.kiem_dinh_nen_doc === "chi2" ? " ← đọc dòng này" : ""), fmt(r.chi2), r.df, fmtP(r.p)],
        ...(r.fisher_p !== null && r.fisher_p !== undefined ? [["Fisher's exact test ← đọc dòng này", "", "", fmtP(r.fisher_p)]] : []),
      ], { num: [1, 2, 3] }),
      h("p", { class: "hint" }, `Cramér's V = ${fmt(r.cramers_v, 3)} · ${lt5} ô (${fmt(r.pct_o_ky_vong_nho, 1)}%) có tần số kỳ vọng < 5 · kỳ vọng nhỏ nhất = ${fmt(r.ky_vong_nho_nhat)}`));
  }
  if (t === "tuong-quan") {
    const vars = r.bien;
    const key = (a, b) => r.cap.find((c) => (c.x === a && c.y === b) || (c.x === b && c.y === a));
    const sym = r.phuong_phap === "spearman" ? "rₛ" : "r";
    const matrix = vars.map((a, i) => [a.label, ...vars.map((b, j) => {
      if (i === j) return "1";
      if (j > i) return "";
      const c = key(a.name, b.name);
      return c && c.r !== null ? h("span", {}, fmt(c.r), c.p <= 0.05 ? " *" : "", h("br"), h("small", { class: "hint" }, `p ${fmtP(c.p)}`)) : "—";
    })]);
    return h("div", {},
      h("p", { class: "hint" }, `Ma trận hệ số ${r.phuong_phap === "spearman" ? "Spearman" : "Pearson"} (${sym}); * là p ≤ ,05.`),
      table(["", ...vars.map((v) => v.label)], matrix, { num: vars.map((_, i) => i + 1) }),
      table(["Biến 1", "Biến 2", "n", sym, "p", "p Bonferroni", "95% CI"],
        r.cap.map((c) => [c.x_label, c.y_label, c.n, fmt(c.r), fmtP(c.p), fmtP(c.p_bonferroni), c.ci95 ? `[${fmt(c.ci95[0])}; ${fmt(c.ci95[1])}]` : "—"]),
        { num: [2, 3, 4, 5] }));
  }
  if (t === "thang-do") {
    return h("div", {}, r.ket_qua_thang_do.map((rep) => {
      const title = rep.scale.ma === "LIKERT" ? "Thang Likert tự xây dựng" : `${rep.scale.ma} – ${rep.scale.ten_viet}`;
      const parts = [h("h3", {}, title)];
      if (rep.trang_thai === "can_xac_nhan") {
        const req = S.scaleReqs.find((x) => x.ma === rep.scale.ma);
        parts.push(h("div", { class: "note warn" }, rep.thong_bao, " ",
          h("button", { class: "btn small primary", onclick: async (e) => busy(e.target, async () => {
            req.dich_chuyen = rep.kiem_tra.lech_ma_hoa.goi_y_tru;
            renderScaleList();
            await runAnalysis(collectParams());
          }) }, `Xác nhận trừ ${rep.kiem_tra.lech_ma_hoa.goi_y_tru}`)));
      } else if (rep.ket_qua) {
        const kt = rep.kiem_tra || {};
        parts.push(table(["Điểm", "n", "M", "SD", "Min", "Max", "Cronbach's α", "Phân bố theo mức"],
          Object.entries(rep.ket_qua).map(([code, k]) => [k.ten, k.n, fmt(k.mean), fmt(k.sd), fmt(k.min), fmt(k.max),
            kt.cronbach && kt.cronbach[code] !== undefined && kt.cronbach[code] !== null ? fmt(kt.cronbach[code]) : "—",
            k.phan_bo_muc ? Object.entries(k.phan_bo_muc).map(([m, p]) => `${m}: ${fmt(p, 1)}%`).join("; ") : "—"]),
          { num: [1, 2, 3, 4, 5, 6] }));
      }
      if (rep.bang_ghep) parts.push(mappingBox("Bảng ghép câu – cột", rep.bang_ghep));
      return h("div", {}, ...parts);
    }));
  }
  return null;
}

function aiBox(r) {
  if (!S.coAI) return null;
  const log = h("div", { class: "chat" });
  const input = h("textarea", { rows: 2, placeholder: "Ví dụ: Vì sao lại đọc dòng Welch?" });
  const msg = h("span", { class: "msg" });
  const btn = h("button", { class: "btn primary small", onclick: () => busy(btn, async () => {
    const q = input.value.trim();
    if (!q) return;
    log.append(h("div", { class: "bubble user" }, q));
    input.value = ""; setMsg(msg, "Đang hỏi…");
    try {
      const res = await api("/giai-thich", { json: { ket_qua: r, cau_hoi: q, lich_su: S.chat } });
      S.chat.push({ role: "user", content: q }, { role: "assistant", content: res.tra_loi });
      log.append(h("div", { class: "bubble ai", html: md(res.tra_loi) }));
      setMsg(msg, "");
    } catch (err) { setMsg(msg, err.message, "err"); }
  }) }, "Hỏi");
  return h("div", { class: "card" }, h("h2", {}, "Hỏi trợ lý AI về kết quả này"),
    h("p", { class: "hint" }, "Trợ lý chỉ nhận bảng kết quả đã tính, không nhận dữ liệu gốc của bạn."), log, input, h("div", { class: "actions" }, btn, msg));
}

function renderResult(r) {
  const box = $("#pt-ket-qua");
  const parts = [h("div", { class: "card result-card" }, h("h2", {}, `Kết quả · ${TEN_PHAN_TICH[r.analysis] || r.analysis}`),
    renderExplanation(r.giai_thich), knowledgeLinks(r.analysis),
    h("details", { open: true }, h("summary", {}, "Bảng số liệu"), renderTables(r)), feedbackPrompt()), aiBox(r)];
  box.replaceChildren(...parts.filter(Boolean));  // replaceChildren(null) sẽ in ra chữ "null"
}

// ---------- Phiếu đánh giá web (ẩn danh) ----------
const dgHop = $("#dg-hop"), dgForm = $("#dg-form");
$$(".dg-thang", dgForm).forEach((box) => box.replaceChildren(...[1, 2, 3, 4, 5].map((n) =>
  h("label", {}, h("input", { type: "radio", name: box.dataset.name, value: n, "aria-label": `${n} điểm` }), h("span", {}, String(n))))));

function openFeedback() {
  setMsg($("#dg-thong-bao"), "");
  if (typeof dgHop.showModal === "function") dgHop.showModal(); else dgHop.setAttribute("open", "");
}
function closeFeedback() { if (typeof dgHop.close === "function") dgHop.close(); else dgHop.removeAttribute("open"); }
$("#dg-mo").addEventListener("click", openFeedback);
$("#dg-dong").addEventListener("click", closeFeedback);

dgForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(dgForm);
  const msg = $("#dg-thong-bao");
  let missing = false;
  $$(".dg-thang", dgForm).forEach((box) => {
    const ok = fd.get(box.dataset.name) !== null;
    box.closest(".dg-cau").classList.toggle("loi", !ok);
    if (!ok) missing = true;
  });
  if (missing) return setMsg(msg, "Vui lòng chọn điểm cho các câu có dấu *.", "err");
  const body = {
    huu_ich: Number(fd.get("huu_ich")), chinh_xac: Number(fd.get("chinh_xac")), de_dung: Number(fd.get("de_dung")),
    doi_chieu: fd.get("doi_chieu") || null, gop_y: (fd.get("gop_y") || "").trim(), vai_tro: fd.get("vai_tro") || null,
    phep_phan_tich: S.lastResult?.analysis || null,
  };
  const btn = $('button[type="submit"]', dgForm);
  await busy(btn, async () => {
    try {
      const r = await api("/danh-gia", { json: body });
      setMsg(msg, r.thong_bao, "ok");
      dgForm.reset();
      try { localStorage.setItem("da-danh-gia", new Date().toISOString()); } catch { /* bộ nhớ trình duyệt bị chặn: bỏ qua */ }
      setTimeout(closeFeedback, 1400);
    } catch (err) { setMsg(msg, err.message, "err"); }
  });
});

/** Lời mời đánh giá nhỏ dưới mỗi kết quả. */
function feedbackPrompt() {
  return h("div", { class: "dg-moi" }, h("span", { class: "hint" }, "Kết quả này có giúp ích cho bạn không? Góp ý của bạn giúp web chính xác và dễ dùng hơn."),
    h("button", { class: "btn small", onclick: openFeedback }, "✍ Đánh giá web"));
}

// ---------- Khởi động ----------
(async function init() {
  addCommonRow({ ten: "GioiTinh", cau_hoi: "Giới tính của bạn", loai: "nhom", lua_chon: ["Nam", "Nữ"] });
  addCommonRow({ ten: "Khoi", cau_hoi: "Bạn đang học khối nào?", loai: "nhom", lua_chon: ["10", "11", "12"] });
  addLikertRow({ ma: "HT", ten: "Hứng thú học tập", so_cau: 4, dao: [4] });
  try {
    const [lib, cfg, rules, knowledge] = await Promise.all([api("/thang-do"), api("/cau-hinh"), api("/rang-buoc"), api("/kien-thuc")]);
    S.library = lib; S.coAI = cfg.co_ai; S.rules = rules;
    renderScaleMenu();
    renderKnowledge(knowledge);
  } catch (err) {
    setMsg($("#tk-thong-bao"), "Không kết nối được máy chủ: " + err.message, "err");
  }
})();
