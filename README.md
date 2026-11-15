# چرا (Chera) — AI Data-to-Decision Copilot

داده‌های پراکندهٔ شرکت (فروش، هزینه، عملیات) را آپلود کن و به فارسی بپرس؛
«چرا» جواب می‌دهد چه اتفاقی افتاده، **چرا** افتاده، و کدام بخش بیشترین سهم را
در تغییر داشته — بدون SQL و بدون صف انتظار تیم فنی.

## ساختار پروژه

```
backend/    بک‌اند FastAPI + pandas (آپلود CSV/Excel، NLU فارسی، تحلیل)
frontend/   رابط چت (HTML/CSS/JS خالص، بدون build) — از همان بک‌اند سرو می‌شود
landing/    لندینگ‌پیج معرفی محصول (استاتیک)
docs/       مستند معماری و نقشهٔ راه فنی
```

## اجرای سریع (محلی)

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

سپس مرورگر را باز کن: **http://localhost:8000** — همان صفحه هم رابط چت است و
هم به API متصل است (چون فرانت‌اند از همین بک‌اند سرو می‌شود).

## اجرا با Docker (روش پیشنهادی)

```bash
cp .env.example .env          # در صورت نیاز پورت میزبان را تغییر بده
docker compose up -d --build
```

- رابط برنامه: **http://localhost:8000**
- لندینگ‌پیج: **http://localhost:8000/landing**
- سلامت سرویس: **http://localhost:8000/api/health**

داده‌های آپلودی در volume نام‌دار `chera-data` (مسیر `/app/backend/data` داخل
کانتینر) نگه داشته می‌شوند و با `docker compose down` از بین نمی‌روند.

```bash
docker compose logs -f app        # مشاهدهٔ لاگ
docker compose down               # توقف (داده حفظ می‌شود)
docker compose down -v            # توقف و حذف کامل داده‌ها
```

پشتیبان‌گیری از داده‌ها:

```bash
docker run --rm -v chera-data:/data -v "$PWD":/backup alpine \
  tar czf /backup/chera-data-backup.tar.gz -C /data .
```

کانتینر با کاربر غیر root اجرا می‌شود و `HEALTHCHECK` روی `/api/health` تنظیم
شده است. برای استقرار روی سرور، پورت ۸۰۰۰ را پشت reverse proxy با HTTPS قرار
بده.

### تست‌ها

```bash
cd backend
.venv/bin/pip install pytest
.venv/bin/python -m pytest tests/ -v
```

### نمونه سؤال‌هایی که می‌توانی بپرسی (بعد از آپلود یک فایل فروش)

- «مجموع فروش چقدر است؟»
- «فروش به تفکیک محصول چقدر است؟»
- «چرا فروش افت کرد؟»
- «روند فروش چطور بوده؟»
- «کمترین فروش در کدام کانال بوده؟»

## نمایش لندینگ‌پیج

`landing/index.html` را مستقیم در مرورگر باز کن، یا با هر static server ساده
سرو کن.

## نکات فنی مهم

- تاریخ‌های شمسی (مثل `۱۴۰۳/۰۱/۰۵`) به‌صورت بومی تشخیص داده و به میلادی تبدیل
  می‌شوند؛ گروه‌بندی ماهانه هم بر اساس مرز واقعی ماه شمسی است، نه میلادی.
- موتور پاسخ‌دهی فعلی **قانون‌محور** است (بدون فراخوانی LLM خارجی) — سریع و
  رایگان برای دستهٔ رایج سؤال‌ها. جزئیات و مسیر افزودن LLM مکمل در
  `docs/ARCHITECTURE.md` بخش ۳ آمده است.
- کنار پاسخ به سؤال، یک **موتور بینش خودکار** (`backend/app/insights.py`) بدون
  هیچ سؤالی مهم‌ترین یافته‌های دیتاست (روند غیرعادی، تمرکز بیش‌ازحد یک دسته،
  گروه دورافتاده، کیفیت داده) را خودش پیدا می‌کند و بعد از انتخاب دیتاست در چت
  نشان می‌دهد — جزئیات در `docs/ARCHITECTURE.md` بخش ۳.۱.

برای معماری کامل، تصمیم‌های طراحی و نقشهٔ راه، `docs/ARCHITECTURE.md` را
بخوان.
