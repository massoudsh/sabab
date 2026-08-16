# Insights Engine

> موتور بینش خودکار — بدون هیچ سؤالی، مستقیم روی دیتافریم اجرا می‌شود و
> مهم‌ترین یافته‌ها را خودش پیدا می‌کند. اولین قدم فاز ۴ نقشهٔ راه («هشدار
> پیش‌فعال»). اضافه‌شده در ۱۴۰۵/۰۵/۲۵ (۲۰۲۶-۰۸-۱۶).

## مسئولیت‌ها
تابع اصلی `generate_insights(df) -> list[dict]` حداکثر ۵ یافته
(`MAX_INSIGHTS`) از ۴ نوع را برمی‌گرداند، مرتب‌شده بر اساس شدت/اهمیت:

| نوع | شرط فلگ شدن | آستانه |
|---|---|---|
| `trend` | تغییر دوره‌به‌دورهٔ یک سنجهٔ عددی | ≥۲۰٪ (`TREND_CHANGE_THRESHOLD`) |
| `concentration` | سهم یک دسته از مجموع یک سنجه | ≥۵۰٪ (`CONCENTRATION_THRESHOLD`) |
| `outlier_group` | فاصلهٔ z-score میانگین یک دسته از بقیه | ≥۲.۰ (`OUTLIER_GROUP_Z`) |
| `data_quality` | نسبت مقدار خالی یک ستون | ≥۲۰٪ (`DATA_QUALITY_MISSING_RATIO`) |

هر ستون عددی/دسته‌ای فقط تا سقف `MAX_NUMERIC_COLS`/`MAX_CATEGORICAL_COLS`
(هر دو = ۵) بررسی می‌شود تا روی دیتاست‌های خیلی wide کند نشود.

## وابستگی‌ها
- [[entities/analytics-engine]] — از `trend_by_period` و `groupby_aggregate`
  مستقیم استفاده می‌کند.
- API: `GET /api/datasets/{id}/insights` در [[entities/backend-api]].
- فرانت‌اند: `app.js: loadInsights` بلافاصله بعد از انتخاب دیتاست فراخوانی
  می‌شود و نتیجه را به‌صورت یک پیام در چت نشان می‌دهد.

## قراردادها / Edge cases
- `outlier_group` نیازمند حداقل ۳ دسته است (کمتر از آن z-score معنی‌دار
  نیست)؛ توجه: با فرمول sample std (`ddof=1`)، حداکثر z ممکن برای n دسته
  عملاً کمی کمتر از `sqrt(n-1)` است — یعنی برای فلگ‌شدن مطمئن با آستانهٔ ۲.۰
  حداقل به ۶ دسته نیاز است.
- خطای محاسباتی روی هر (metric, group) به‌صورت مجزا catch می‌شود تا کل موتور
  با یک ستون بد شکست نخورد.
- دیتافریم خالی → لیست خالی (بدون خطا).

## منابع کد
- `backend/app/insights.py`
- تست: `backend/tests/test_insights.py`
- معماری کامل: `docs/ARCHITECTURE.md` بخش ۳.۱
