# Frontend Chat UI

> HTML/CSS/JS خالص، بدون فریم‌ورک و بدون مرحلهٔ build؛ از همان FastAPI backend
> به‌صورت static سرو می‌شود.

## مسئولیت‌ها
- آپلود فایل → `loadDatasets` → انتخاب دیتاست (`selectDataset`).
- بعد از انتخاب دیتاست: هم پیام خوش‌آمد + جزئیات (`renderDatasetDetail`) و هم
  فراخوانی خودکار موتور بینش (`loadInsights` → `renderInsightsMessage`) —
  نگاه کنید [[entities/insights-engine]].
- فرم پرسش (`ask-form`) → `POST /api/ask` → رندر پاسخ + جدول + نمودار
  (Chart.js) در `addBotMessage`.

## وابستگی‌ها
- [[entities/backend-api]] — تنها از طریق `fetch` با آن ارتباط دارد،
  آدرس با `API_BASE` قابل تغییر است (پیش‌فرض خالی = هم‌مبدأ).

## قراردادها / Edge cases
- `chart.type === "line"` → نمودار خطی، در غیر این صورت میله‌ای.
- خروجی‌های `warning` موتور بینش با کلاس CSS `severity-warning` رنگ متفاوت
  می‌گیرند (`style.css`).

## منابع کد
- `frontend/app.js`, `frontend/index.html`, `frontend/style.css`
