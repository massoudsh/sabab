const API_BASE = "";
const fa = (value) => String(value).replace(/\d/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[digit]);
const number = (value) => Number(value || 0).toLocaleString("fa-IR");
const state = { datasets: [], currentDatasetId: null, currentDetail: null, currentInsights: [] };
const titles = { dashboard: "نمای کلی", datasets: "دیتاست‌ها", insights: "بینش‌ها", reports: "گزارش‌ها", settings: "تنظیمات" };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const el = { file: $("#file-input"), status: $("#upload-status"), list: $("#dataset-list"), count: $("#dataset-count"), toast: $("#toast") };

async function api(path, options) {
  const response = await fetch(API_BASE + path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "خطای غیرمنتظره از سرور");
  return data;
}
function escapeHtml(value) { const div = document.createElement("div"); div.textContent = value ?? ""; return div.innerHTML; }
function showToast(message) { el.toast.textContent = message; el.toast.classList.add("show"); window.clearTimeout(showToast.timer); showToast.timer = window.setTimeout(() => el.toast.classList.remove("show"), 3200); }
function switchView(view) { $$(".view").forEach((item) => item.classList.toggle("active", item.id === `view-${view}`)); $$(".nav-item[data-view]").forEach((item) => item.classList.toggle("active", item.dataset.view === view)); $("#page-title").textContent = titles[view]; $("#current-section").textContent = titles[view]; if (view === "datasets") renderDatasetsTable(); if (view === "insights") renderInsightsPage(); if (view === "reports") renderReport(); }

async function loadDatasets() {
  try { state.datasets = await api("/api/datasets"); renderDatasetList(); renderStats(); renderDatasetsTable(); fillInsightSelect(); if (!state.currentDatasetId && state.datasets[0]) await selectDataset(state.datasets[0].id, false); else if (!state.datasets.length) renderEmptyState(); }
  catch (error) { showToast(error.message); }
}
function renderDatasetList() {
  el.list.innerHTML = state.datasets.length ? state.datasets.map((dataset) => `<li class="${dataset.id === state.currentDatasetId ? "active" : ""}" data-id="${escapeHtml(dataset.id)}"><span>${escapeHtml(dataset.name)}</span><span class="rows-badge">${fa(dataset.rows)}</span></li>`).join("") : '<li class="muted-text">هنوز دیتاستی ندارید</li>';
  el.count.textContent = fa(state.datasets.length);
  $$("#dataset-list li[data-id]").forEach((item) => item.addEventListener("click", () => selectDataset(item.dataset.id)));
}
function renderStats() {
  const rows = state.datasets.reduce((total, dataset) => total + dataset.rows, 0);
  const columns = state.datasets.reduce((total, dataset) => total + dataset.columns.length, 0);
  $("#overview-stats").innerHTML = [{ label: "دیتاست فعال", value: state.datasets.length, icon: "▤", color: "#e9e8ff" }, { label: "کل سطرهای داده", value: rows, icon: "↗", color: "#def8f2" }, { label: "ستون‌های قابل تحلیل", value: columns, icon: "◈", color: "#fff1d9" }, { label: "وضعیت تحلیل", value: state.datasets.length ? "آماده" : "—", icon: "✦", color: "#ffe5e5" }].map((stat) => `<div class="stat-card" style="--stat-color:${stat.color}"><span class="stat-label">${stat.label}</span><strong class="stat-value">${typeof stat.value === "number" ? fa(number(stat.value)) : stat.value}</strong><span class="stat-icon">${stat.icon}</span></div>`).join("");
}
async function selectDataset(id, notify = true) {
  state.currentDatasetId = id; renderDatasetList();
  try { state.currentDetail = await api(`/api/datasets/${id}`); state.currentInsights = await api(`/api/datasets/${id}/insights`); if (notify) showToast(`دیتاست «${state.currentDetail.name}» انتخاب شد`); renderDashboard(); renderInsightsPage(); renderReport(); }
  catch (error) { showToast(error.message); }
}
function renderDashboard() {
  const detail = state.currentDetail;
  $("#dashboard-chat").innerHTML = detail ? `<div class="msg bot"><div class="bubble">دیتاست «${escapeHtml(detail.name)}» آماده است. ${fa(detail.rows)} سطر و ${fa(detail.columns.length)} ستون برای تحلیل داریم.</div></div>` : '<div class="empty-chat"><div><strong>هنوز دیتاستی انتخاب نشده است</strong><span>با افزودن یک فایل، گفت‌وگوی تحلیلی را شروع کنید.</span></div></div>';
  renderInsightStack($("#dashboard-insights"), state.currentInsights.slice(0, 3));
}
function insightClass(insight) { return insight.severity === "warning" ? "warning" : insight.severity === "critical" ? "critical" : ""; }
function insightLabel(type) { return ({ trend: "روند", concentration: "تمرکز", outlier: "دادهٔ متفاوت", quality: "کیفیت داده" })[type] || "بینش خودکار"; }
function renderInsightStack(target, insights) { target.innerHTML = insights.length ? insights.map((insight) => `<div class="insight-item ${insightClass(insight)}"><span class="insight-type">${insightLabel(insight.type)}</span>${escapeHtml(insight.narrative)}</div>`).join("") : '<div class="empty-chat"><div><strong>بینشی برای نمایش نیست</strong><span>یک دیتاست معتبر انتخاب کنید.</span></div></div>'; }
function fillInsightSelect() { const select = $("#insight-dataset-select"); select.innerHTML = state.datasets.map((dataset) => `<option value="${escapeHtml(dataset.id)}" ${dataset.id === state.currentDatasetId ? "selected" : ""}>${escapeHtml(dataset.name)}</option>`).join(""); }
async function renderInsightsPage() { fillInsightSelect(); const subtitle = $("#insights-subtitle"); if (!state.currentDetail) { subtitle.textContent = "دیتاستی را انتخاب کنید تا مهم‌ترین یافته‌ها نمایش داده شوند."; $("#insights-grid").innerHTML = '<div class="empty-state"><div class="empty-icon">✦</div><h3>هنوز داده‌ای برای تحلیل نیست</h3><p>یک دیتاست اضافه کنید تا بینش‌ها ساخته شوند.</p></div>'; return; } subtitle.textContent = `یافته‌های استخراج‌شده از «${state.currentDetail.name}»`; const target = $("#insights-grid"); target.innerHTML = state.currentInsights.length ? state.currentInsights.map((insight, index) => `<article class="insight-card ${insightClass(insight)}"><div class="insight-card-header"><span>${insightLabel(insight.type)}</span><span class="status-badge">${insight.severity === "warning" ? "نیازمند توجه" : "بررسی‌شده"}</span></div><p>${escapeHtml(insight.narrative)}</p>${insight.chart ? `<div class="insight-chart" id="insight-chart-${index}"></div>` : ""}</article>`).join("") : '<div class="empty-state"><div class="empty-icon">✓</div><h3>یافتهٔ خاصی شناسایی نشد</h3><p>این دیتاست فعلاً الگوی غیرعادی قابل‌توجهی ندارد.</p></div>'; state.currentInsights.forEach((insight, index) => { if (insight.chart) renderChart(insight.chart, $(`#insight-chart-${index}`)); }); }
function renderDatasetsTable() { const query = ($( "#dataset-search")?.value || "").trim().toLowerCase(); const datasets = state.datasets.filter((dataset) => dataset.name.toLowerCase().includes(query)); $("#dataset-table-count").textContent = `${fa(datasets.length)} دیتاست`; $("#datasets-empty").classList.toggle("hidden", datasets.length > 0); $(".dataset-table").classList.toggle("hidden", datasets.length === 0); $("#datasets-table-body").innerHTML = datasets.map((dataset) => `<tr><td><div class="dataset-name">${escapeHtml(dataset.name)}</div><div class="dataset-meta">شناسه: ${escapeHtml(dataset.id.slice(0, 8))}</div></td><td>${fa(number(dataset.rows))}</td><td>${fa(number(dataset.columns.length))}</td><td>${escapeHtml(dataset.uploaded_at || "—")}</td><td><span class="status-badge">آماده تحلیل</span></td><td><button class="table-action" type="button" data-select-id="${escapeHtml(dataset.id)}">مشاهده</button></td></tr>`).join(""); $$("[data-select-id]").forEach((button) => button.addEventListener("click", () => { selectDataset(button.dataset.selectId); switchView("dashboard"); })); }
function renderEmptyState() { renderDashboard(); renderInsightsPage(); renderReport(); }
function renderReport() { const target = $("#report-content"); const detail = state.currentDetail; if (!detail) { target.innerHTML = '<div class="panel empty-state"><div class="empty-icon">▥</div><h3>گزارشی برای نمایش نیست</h3><p>یک دیتاست را انتخاب کنید تا گزارش آن ساخته شود.</p></div>'; return; } target.innerHTML = `<div class="report-grid"><div class="report-card"><small>نام دیتاست</small><strong>${escapeHtml(detail.name)}</strong></div><div class="report-card"><small>تعداد سطر</small><strong>${fa(number(detail.rows))}</strong></div><div class="report-card"><small>ستون‌های عددی</small><strong>${fa(number(detail.numeric_columns.length))}</strong></div></div><div class="panel report-preview"><h3>پیش‌نمایش داده</h3><p class="muted-text">پنج سطر اول دیتاست برای بررسی سریع ساختار داده</p><div class="table-scroll">${detail.preview?.length ? renderTable(detail.preview) : '<div class="empty-state">پیش‌نمایشی وجود ندارد.</div>'}</div></div>`; }
function renderTable(rows) { const columns = Object.keys(rows[0]); return `<table class="data-table"><thead><tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${columns.map((column) => `<td>${escapeHtml(formatCell(row[column]))}</td>`).join("")}</tr>`).join("")}</tbody></table>`; }
function formatCell(value) { return typeof value === "number" ? number(value) : String(value ?? "—"); }
let chartCounter = 0;
function renderChart(chart, target) { if (!target || typeof Chart === "undefined") return; const canvas = document.createElement("canvas"); target.appendChild(canvas); const colors = ["#635bdf", "#16b8a6", "#f59e0b", "#ef6a6a"]; new Chart(canvas.getContext("2d"), { type: chart.type === "line" ? "line" : "bar", data: { labels: chart.labels, datasets: chart.series.map((series, index) => ({ label: series.name, data: series.data, backgroundColor: chart.type === "line" ? "transparent" : colors[index % colors.length], borderColor: colors[index % colors.length], borderWidth: 2, tension: .3 })) }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: "#718096", font: { family: "Tahoma" } } } }, scales: { x: { ticks: { color: "#8995a8" }, grid: { color: "#eef0f5" } }, y: { ticks: { color: "#8995a8" }, grid: { color: "#eef0f5" } } } } }); chartCounter += 1; }

async function askQuestion(question) { if (!state.currentDatasetId) { showToast("ابتدا یک دیتاست اضافه کنید"); switchView("datasets"); return; } const form = $("#ask-form"); const input = $("#question-input"); input.disabled = true; $("#dashboard-chat").insertAdjacentHTML("beforeend", `<div class="msg user"><div class="bubble">${escapeHtml(question)}</div></div>`); try { const result = await api("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ dataset_id: state.currentDatasetId, question }) }); const content = `<div class="msg bot"><div class="msg-content"><div class="bubble">${escapeHtml(result.answer)}</div>${result.table?.length ? `<div class="response-table">${renderTable(result.table)}</div>` : ""}${result.chart ? '<div class="chart-wrap" id="answer-chart"></div>' : ""}</div></div>`; $("#dashboard-chat").insertAdjacentHTML("beforeend", content); if (result.chart) renderChart(result.chart, $("#answer-chart")); } catch (error) { $("#dashboard-chat").insertAdjacentHTML("beforeend", `<div class="msg bot"><div class="bubble">${escapeHtml(error.message)}</div></div>`); } finally { input.disabled = false; input.focus(); form.reset(); } }
async function uploadFile() { const file = el.file.files[0]; if (!file) return; el.status.textContent = "در حال بارگذاری…"; try { const formData = new FormData(); formData.append("file", file); const meta = await api("/api/datasets/upload", { method: "POST", body: formData }); el.status.textContent = `«${meta.name}» اضافه شد`; await loadDatasets(); await selectDataset(meta.id); showToast("دیتاست با موفقیت اضافه شد"); } catch (error) { el.status.textContent = error.message; el.status.className = "upload-status error"; } finally { el.file.value = ""; } }

$$('[data-view]').forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
$$('[data-view-link]').forEach((button) => button.addEventListener("click", () => switchView(button.dataset.viewLink)));
$$('.upload-trigger').forEach((button) => button.addEventListener("click", () => el.file.click()));
el.file.addEventListener("change", uploadFile);
$("#ask-form").addEventListener("submit", (event) => { event.preventDefault(); const question = $("#question-input").value.trim(); if (question) askQuestion(question); });
$$('[data-question]').forEach((button) => button.addEventListener("click", () => { $("#question-input").value = button.dataset.question; $("#question-input").focus(); }));
$("#dataset-search").addEventListener("input", renderDatasetsTable);
$("#insight-dataset-select").addEventListener("change", (event) => selectDataset(event.target.value, false));
$("#print-report").addEventListener("click", () => window.print());
loadDatasets();
