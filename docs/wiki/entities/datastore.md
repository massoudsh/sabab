# Datastore

> مدیریت ذخیره و بازیابی دیتاست‌های آپلودشده — MVP: pickle روی دیسک + مانیفست
> JSON. **نه برای production چندمستأجری.**

## مسئولیت‌ها
- خواندن CSV/TSV (با تلاش چند encoding: utf-8-sig, utf-8, cp1256, latin-1) و
  Excel (`_read_tabular`).
- ذخیرهٔ هر دیتاست به‌صورت `DataFrame.to_pickle` در `backend/data/{id}.pkl` +
  رکورد در `manifest.json` (`save_upload`).
- CRUD: `list_datasets`, `get_meta`, `load_dataframe`, `delete_dataset`.

## قراردادها / Edge cases
- سقف امنیتی MVP: حداکثر ۲۵MB حجم فایل، ۲۰۰,۰۰۰ سطر (سطرهای مازاد قطع
  می‌شوند، نه رد).
- فایل خالی → `DatasetError`.
- شناسهٔ دیتاست: `uuid4().hex[:12]`.

## وابستگی‌ها
- تمام entityهای دیگر (`analytics`, `nlu`, `insights`) از طریق
  `load_dataframe` دیتافریم می‌گیرند؛ خودشان هیچ I/O مستقیمی ندارند.

## گام بعدی (نقشهٔ راه)
جایگزینی با Postgres (متادیتا) + DuckDB/Parquet (داده)، اتصال زندهٔ دیتابیس/
CRM/شیت — نگاه کنید [[concepts/roadmap]] فاز ۲ و ۴.

## منابع کد
- `backend/app/datastore.py`
