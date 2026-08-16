# Backend API

> FastAPI app (`backend/app/main.py`) — همهٔ مسیرهای `/api/*` + سرو استاتیک
> فرانت‌اند از همان اپ.

## مسیرها (routes)
| متد | مسیر | توضیح |
|---|---|---|
| GET | `/api/health` | health check |
| POST | `/api/datasets/upload` | آپلود CSV/Excel → `DatasetMeta` |
| GET | `/api/datasets` | لیست دیتاست‌ها |
| GET | `/api/datasets/{id}` | جزئیات + preview + ستون‌ها → `DatasetDetail` |
| GET | `/api/datasets/{id}/insights` | یافته‌های خودکار → `list[Insight]` |
| DELETE | `/api/datasets/{id}` | حذف دیتاست |
| POST | `/api/ask` | سؤال فارسی → `AskResponse` |
| `/` | (mount استاتیک) | فرانت‌اند `frontend/` — باید **بعد از** همهٔ مسیرهای `/api` mount شود |

## وابستگی‌ها
- [[entities/datastore]], [[entities/nlu-engine]], [[entities/analytics-engine]],
  [[entities/insights-engine]]

## قراردادها / Edge cases
- CORS باز (`allow_origins=["*"]`) — مناسب MVP دمو، نه production.
- مدل‌های Pydantic ورودی/خروجی در `schemas.py` (`AskRequest`, `AskResponse`,
  `Insight`, `DatasetMeta`, `DatasetDetail`, `ChartData`).

## منابع کد
- `backend/app/main.py`, `backend/app/schemas.py`
