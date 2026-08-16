# Persian Date Handling

> تصمیم معماری: تاریخ شمسی باید قبل از هر تحلیل به میلادی تبدیل شود، و
> گروه‌بندی ماهانه باید روی مرز واقعی ماه شمسی باشد — نه میلادی.

## چرا لازم است
`pandas.Timestamp` فقط سال‌های میلادی ۱۶۷۷ تا ۲۲۶۲ را پشتیبانی می‌کند و از
تاریخ شمسی سر در نمی‌آورد. داده‌های کسب‌وکار ایرانی معمولاً با فرمت شمسی
(مثل `۱۴۰۳/۰۱/۰۵`) هستند.

## پیاده‌سازی
- `jalali.is_jalali_series` تشخیص می‌دهد یک ستون رشته‌ای شمسی است یا نه.
- `jalali.parse_jalali_series` تبدیل به `datetime64` میلادی (با کتابخانهٔ
  `jdatetime`).
- `jalali.to_period_label` برچسب دورهٔ ماهانه را روی **مرز واقعی ماه شمسی**
  می‌سازد (نه `dt.to_period("M")` میلادی که مرز اشتباه می‌دهد).

## کجا استفاده می‌شود
- [[entities/analytics-engine]]: `as_datetime`, `detect_date_columns`,
  `explain_change`, `trend_by_period` — همه از این لایه عبور می‌کنند.
- [[entities/insights-engine]]: بینش `trend` مستقیم روی خروجی
  `trend_by_period` سوار است، پس این منطق را رایگان به ارث می‌برد.

## منابع کد
- `backend/app/jalali.py`
- تست‌های مرتبط: `backend/tests/test_analytics.py`
