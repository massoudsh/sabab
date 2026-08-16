# Analytics Engine

> موتور تحلیل روی داده جدولی (pandas)؛ بدون وابستگی به LLM خارجی.

## مسئولیت‌ها
- تشخیص ستون‌های تاریخ/عددی/دسته‌ای (`detect_date_columns`, `numeric_columns`,
  `categorical_columns`).
- تجمیع ساده (`aggregate_column`) و گروه‌بندی/رتبه‌بندی (`groupby_aggregate`).
- تجزیهٔ تغییر یک شاخص بین دو دورهٔ اخیر به تفکیک یک بُعد (`explain_change`) —
  قلب ویژگی «چرا» محصول.
- روند زمانی یک سنجه بر اساس دورهٔ شمسی (`trend_by_period`).
- خلاصهٔ یک دیتاست برای preview (`describe`).

## وابستگی‌ها
- [[concepts/persian-date-handling]] — همهٔ فیلترهای تاریخ‌دار از `jalali.py`
  عبور می‌کنند.
- [[entities/nlu-engine]] — intent تشخیص‌داده‌شده را به یکی از توابع این ماژول
  می‌سپارد.
- [[entities/insights-engine]] — روی همین توابع (`trend_by_period`,
  `groupby_aggregate`) سوار شده تا بدون سؤال هم یافته تولید کند.

## قراردادها / Edge cases
- `explain_change` همیشه **دو دورهٔ آخر** موجود در داده را مقایسه می‌کند، نه
  بازهٔ دلخواه.
- `groupby_aggregate` با `func in ("max","min")` روی سطح گروه اجرا می‌شود نه
  تک‌رکورد — یعنی «کمترین فروش کانال X» یعنی کمترین **مجموع** آن کانال.
- `_fmt` اعداد صحیح را بدون اعشار و بقیه را با دو رقم اعشار فرمت می‌کند.

## منابع کد
- `backend/app/analytics.py`
- تست: `backend/tests/test_analytics.py`
