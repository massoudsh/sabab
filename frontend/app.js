// اگر فرانت‌اند را جدا از بک‌اند سرو می‌کنید (مثلاً با یک static server ساده)،
// این مقدار را به آدرس بک‌اند تغییر دهید؛ در حالت پیش‌فرض (سرو شدن از همان FastAPI) خالی بماند.
const API_BASE = "";

const state = {
  datasets: [],
  currentDatasetId: null,
};

const el = {
  fileInput: document.getElementById("file-input"),
  uploadStatus: document.getElementById("upload-status"),
  datasetList: document.getElementById("dataset-list"),
  datasetDetail: document.getElementById("dataset-detail"),
  messages: document.getElementById("messages"),
  askForm: document.getElementById("ask-form"),
  questionInput: document.getElementById("question-input"),
};

async function api(path, options) {
  const res = await fetch(API_BASE + path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || "خطای غیرمنتظره از سرور");
  }
  return data;
}

async function loadDatasets() {
  try {
    state.datasets = await api("/api/datasets");
    renderDatasetList();
  } catch (err) {
    console.error(err);
  }
}

function renderDatasetList() {
  el.datasetList.innerHTML = "";
  if (state.datasets.length === 0) {
    const li = document.createElement("li");
    li.textContent = "هنوز دیتاستی آپلود نکرده‌اید";
    li.style.cursor = "default";
    el.datasetList.appendChild(li);
    return;
  }
  for (const ds of state.datasets) {
    const li = document.createElement("li");
    li.className = ds.id === state.currentDatasetId ? "active" : "";
    li.innerHTML = `<span>${escapeHtml(ds.name)}</span><span class="rows-badge">${ds.rows} سطر</span>`;
    li.addEventListener("click", () => selectDataset(ds.id));
    el.datasetList.appendChild(li);
  }
}

async function selectDataset(id) {
  state.currentDatasetId = id;
  renderDatasetList();
  try {
    const detail = await api(`/api/datasets/${id}`);
    renderDatasetDetail(detail);
    addBotMessage(
      `دیتاست «${detail.name}» انتخاب شد (${detail.rows} سطر، ستون‌ها: ${detail.columns.join("، ")}). حالا می‌توانی سؤالت را بپرسی.`
    );
  } catch (err) {
    addBotMessage("خطا در دریافت جزئیات دیتاست: " + err.message, true);
  }
}

function renderDatasetDetail(detail) {
  el.datasetDetail.innerHTML = `
    <div><b>ستون‌های عددی:</b> ${detail.numeric_columns.join("، ") || "—"}</div>
    <div><b>ستون‌های تاریخ:</b> ${detail.date_columns.join("، ") || "—"}</div>
  `;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// --- Upload ---
el.fileInput.addEventListener("change", async () => {
  const file = el.fileInput.files[0];
  if (!file) return;
  el.uploadStatus.textContent = "در حال آپلود...";
  el.uploadStatus.className = "upload-status";
  const formData = new FormData();
  formData.append("file", file);
  try {
    const meta = await api("/api/datasets/upload", { method: "POST", body: formData });
    el.uploadStatus.textContent = `«${meta.name}» با موفقیت آپلود شد.`;
    await loadDatasets();
    await selectDataset(meta.id);
  } catch (err) {
    el.uploadStatus.textContent = err.message;
    el.uploadStatus.className = "upload-status error";
  } finally {
    el.fileInput.value = "";
  }
});

// --- Chat ---
function addUserMessage(text) {
  const wrap = document.createElement("div");
  wrap.className = "msg user";
  wrap.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
  el.messages.appendChild(wrap);
  scrollToBottom();
}

function addBotMessage(text, isFallback = false, table = null, chart = null) {
  const wrap = document.createElement("div");
  wrap.className = "msg bot" + (isFallback ? " fallback" : "");

  const content = document.createElement("div");
  content.className = "msg-content";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  content.appendChild(bubble);

  if (table && table.length > 0) {
    content.appendChild(renderTable(table));
  }
  if (chart && chart.labels && chart.labels.length > 0) {
    content.appendChild(renderChart(chart));
  }

  wrap.appendChild(content);
  el.messages.appendChild(wrap);
  scrollToBottom();
}

function renderTable(rows) {
  const cols = Object.keys(rows[0]);
  const table = document.createElement("table");
  table.className = "data-table";
  const thead = document.createElement("thead");
  thead.innerHTML = `<tr>${cols.map((c) => `<th>${escapeHtml(c)}</th>`).join("")}</tr>`;
  table.appendChild(thead);
  const tbody = document.createElement("tbody");
  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = cols
      .map((c) => `<td>${escapeHtml(formatCell(row[c]))}</td>`)
      .join("");
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  return table;
}

function formatCell(value) {
  if (typeof value === "number") {
    return value.toLocaleString("en-US");
  }
  return String(value);
}

let chartCounter = 0;
function renderChart(chart) {
  const wrap = document.createElement("div");
  wrap.className = "chart-wrap";
  const canvas = document.createElement("canvas");
  canvas.id = "chart-" + chartCounter++;
  wrap.appendChild(canvas);

  const colors = ["#6c5ce7", "#00d4b5", "#ff9f43", "#ff6b6b", "#54a0ff"];
  new Chart(canvas.getContext("2d"), {
    type: chart.type === "line" ? "line" : "bar",
    data: {
      labels: chart.labels,
      datasets: chart.series.map((s, i) => ({
        label: s.name,
        data: s.data,
        backgroundColor: chart.type === "line" ? "transparent" : colors[i % colors.length],
        borderColor: colors[i % colors.length],
        tension: 0.3,
      })),
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: "#e8eaed" } },
      },
      scales: {
        x: { ticks: { color: "#9aa2b1" }, grid: { color: "#2a2f3a" } },
        y: { ticks: { color: "#9aa2b1" }, grid: { color: "#2a2f3a" } },
      },
    },
  });
  return wrap;
}

function scrollToBottom() {
  el.messages.scrollTop = el.messages.scrollHeight;
}

el.askForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = el.questionInput.value.trim();
  if (!question) return;
  if (!state.currentDatasetId) {
    addBotMessage("اول یک فایل CSV یا Excel آپلود کن تا بتوانم سؤالت را جواب بدهم.", true);
    return;
  }
  addUserMessage(question);
  el.questionInput.value = "";
  el.questionInput.disabled = true;

  try {
    const res = await api("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset_id: state.currentDatasetId, question }),
    });
    addBotMessage(res.answer, !res.ok, res.table, res.chart);
  } catch (err) {
    addBotMessage("خطا: " + err.message, true);
  } finally {
    el.questionInput.disabled = false;
    el.questionInput.focus();
  }
});

loadDatasets();
