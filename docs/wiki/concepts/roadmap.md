# Roadmap

> خلاصهٔ نقشهٔ راه محصول؛ جزئیات کامل هر فاز در `docs/ARCHITECTURE.md` بخش ۸.
> ایشوهای گیت‌هاب مرتبط پایین هر فاز لینک شده‌اند (repo: `massoudsh/sabab`).

## فاز ۱ (فعلی/انجام‌شده) — MVP تک‌کاربره
آپلود فایل + NLU قانون‌محور ([[entities/nlu-engine]]) + توضیح تغییر
([[entities/analytics-engine]]) + موتور بینش خودکار ([[entities/insights-engine]]).

## فاز ۲ — چندکاربره
- احراز هویت + ذخیره‌سازی دائمی (Postgres/DuckDB به‌جای pickle) —
  [issue #1](https://github.com/massoudsh/sabab/issues/1)
- تاریخچهٔ گفتگو — [issue #2](https://github.com/massoudsh/sabab/issues/2)

## فاز ۳ — لایهٔ LLM مکمل
سؤال‌های خارج از پوشش rule-based، با sandbox اجرای کوئری —
[issue #3](https://github.com/massoudsh/sabab/issues/3). جزئیات:
[[concepts/rule-based-nlu]].

## فاز ۴ — دادهٔ زنده + هشدار پیش‌فعال
- هشدار پیش‌فعال زنده + پیشنهاد اقدام —
  [issue #4](https://github.com/massoudsh/sabab/issues/4)
- اتصال مستقیم به منابع دادهٔ زنده (دیتابیس/CRM/شیت) —
  [issue #5](https://github.com/massoudsh/sabab/issues/5)
- گام اول این فاز (موتور بینش خودکار) در فاز ۱ پیاده‌سازی شده؛ بهبودهای بعدی:
  [issue #7](https://github.com/massoudsh/sabab/issues/7)

## فاز ۵ — Enterprise
چندمستأجری کامل، RBAC، audit log، استقرار on-premise —
[issue #6](https://github.com/massoudsh/sabab/issues/6)
