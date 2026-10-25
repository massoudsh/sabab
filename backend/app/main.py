from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import analytics, datastore, insights, nlu, workspace
from .schemas import (
    AlertCreate,
    AskRequest,
    AskResponse,
    CommentCreate,
    ConnectionCreate,
    DashboardCreate,
    DatasetDetail,
    DatasetMeta,
    Insight,
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

app = FastAPI(
    title="چرا (Chera) — AI Data-to-Decision Copilot",
    description="MVP بک‌اند: آپلود CSV/Excel و پاسخ به سؤال فارسی درباره‌ی داده.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


def _require_dataset(dataset_id: str) -> tuple[dict, object]:
    meta = datastore.get_meta(dataset_id)
    if not meta:
        raise HTTPException(status_code=404, detail="دیتاست پیدا نشد.")
    return meta, datastore.load_dataframe(dataset_id)


@app.get("/api/connections")
def list_connections():
    return workspace.list_records("connections")


@app.post("/api/connections")
def create_connection(payload: ConnectionCreate):
    meta = datastore.get_meta(payload.dataset_id)
    if not meta:
        raise HTTPException(status_code=404, detail="دیتاست پیدا نشد.")
    return workspace.add_record("connections", payload.model_dump())


@app.post("/api/connections/{connection_id}/sync")
def sync_connection(connection_id: str):
    connection = next((item for item in workspace.list_records("connections") if item["id"] == connection_id), None)
    if not connection:
        raise HTTPException(status_code=404, detail="اتصال پیدا نشد.")
    meta = datastore.get_meta(connection["dataset_id"])
    if not meta:
        raise HTTPException(status_code=404, detail="دیتاست منبع پیدا نشد.")
    return {"ok": True, "connection": connection, "synced_at": meta["uploaded_at"], "rows": meta["rows"]}


@app.get("/api/dashboards")
def list_dashboards():
    return workspace.list_records("dashboards")


@app.post("/api/dashboards")
def create_dashboard(payload: DashboardCreate):
    _require_dataset(payload.dataset_id)
    return workspace.add_record("dashboards", payload.model_dump())


@app.delete("/api/dashboards/{dashboard_id}")
def delete_dashboard(dashboard_id: str):
    if not workspace.delete_record("dashboards", dashboard_id):
        raise HTTPException(status_code=404, detail="داشبورد پیدا نشد.")
    return {"ok": True}


@app.get("/api/alerts")
def list_alerts():
    alerts = []
    for alert in workspace.list_records("alerts"):
        try:
            _, df = _require_dataset(alert["dataset_id"])
            value = analytics.aggregate_column(df, alert["metric_col"], "mean")
            triggered = value is not None and ((alert["direction"] == "below" and value < alert["threshold"]) or (alert["direction"] == "above" and value > alert["threshold"]))
            alerts.append({**alert, "current_value": value, "triggered": triggered})
        except (KeyError, datastore.DatasetError):
            alerts.append({**alert, "current_value": None, "triggered": False})
    return alerts


@app.post("/api/alerts")
def create_alert(payload: AlertCreate):
    _, df = _require_dataset(payload.dataset_id)
    if payload.metric_col not in analytics.numeric_columns(df):
        raise HTTPException(status_code=400, detail="ستون هشدار باید عددی باشد.")
    if payload.direction not in ("below", "above"):
        raise HTTPException(status_code=400, detail="جهت هشدار باید above یا below باشد.")
    return workspace.add_record("alerts", payload.model_dump())


@app.delete("/api/alerts/{alert_id}")
def delete_alert(alert_id: str):
    if not workspace.delete_record("alerts", alert_id):
        raise HTTPException(status_code=404, detail="هشدار پیدا نشد.")
    return {"ok": True}


@app.get("/api/datasets/{dataset_id}/kpis")
def get_kpis(dataset_id: str):
    _, df = _require_dataset(dataset_id)
    cards = []
    for column in analytics.numeric_columns(df)[:8]:
        value = analytics.aggregate_column(df, column, "sum")
        average = analytics.aggregate_column(df, column, "mean")
        cards.append({"name": column, "sum": value, "average": average, "unit": "مقدار"})
    return cards


@app.get("/api/datasets/{dataset_id}/forecast")
def forecast(dataset_id: str, metric_col: str, date_col: str, periods: int = 3):
    _, df = _require_dataset(dataset_id)
    if periods < 1 or periods > 12:
        raise HTTPException(status_code=400, detail="تعداد دوره‌های پیش‌بینی باید بین ۱ تا ۱۲ باشد.")
    result = analytics.forecast_by_period(df, metric_col, date_col, periods)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["reason"])
    return result


@app.get("/api/comments")
def list_comments(dataset_id: str | None = None):
    comments = workspace.list_records("comments")
    return [comment for comment in comments if not dataset_id or comment["dataset_id"] == dataset_id]


@app.post("/api/comments")
def create_comment(payload: CommentCreate):
    _require_dataset(payload.dataset_id)
    if not payload.body.strip() or not payload.author.strip():
        raise HTTPException(status_code=400, detail="نام و متن کامنت الزامی است.")
    return workspace.add_record("comments", {**payload.model_dump(), "body": payload.body.strip(), "author": payload.author.strip()})


@app.post("/api/datasets/upload", response_model=DatasetMeta)
async def upload_dataset(file: UploadFile = File(...)):
    content = await file.read()
    try:
        meta = datastore.save_upload(file.filename or "upload", content)
    except datastore.DatasetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return meta


@app.get("/api/datasets", response_model=list[DatasetMeta])
def list_datasets():
    return datastore.list_datasets()


@app.get("/api/datasets/{dataset_id}", response_model=DatasetDetail)
def get_dataset(dataset_id: str):
    meta = datastore.get_meta(dataset_id)
    if not meta:
        raise HTTPException(status_code=404, detail="دیتاست پیدا نشد.")
    df = datastore.load_dataframe(dataset_id)
    desc = analytics.describe(df)
    return {**meta, "preview": desc["preview"], "numeric_columns": desc["numeric_columns"], "date_columns": desc["date_columns"]}


@app.get("/api/datasets/{dataset_id}/insights", response_model=list[Insight])
def get_insights(dataset_id: str):
    meta = datastore.get_meta(dataset_id)
    if not meta:
        raise HTTPException(status_code=404, detail="دیتاست پیدا نشد.")
    df = datastore.load_dataframe(dataset_id)
    return insights.generate_insights(df)


@app.delete("/api/datasets/{dataset_id}")
def delete_dataset(dataset_id: str):
    try:
        datastore.delete_dataset(dataset_id)
    except datastore.DatasetError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    meta = datastore.get_meta(payload.dataset_id)
    if not meta:
        raise HTTPException(status_code=404, detail="دیتاست پیدا نشد.")
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="سؤال نمی‌تواند خالی باشد.")

    df = datastore.load_dataframe(payload.dataset_id)
    intent = nlu.parse_question(payload.question, df)

    if intent.kind == "aggregate":
        value = analytics.aggregate_column(df, intent.metric_col, intent.func)
        label = analytics.FA_FUNC_LABEL.get(intent.func, intent.func)
        answer = f"{label} «{intent.metric_col}» برابر است با {analytics._fmt(value)}."
        return AskResponse(ok=True, intent=intent.kind, answer=answer)

    if intent.kind == "groupby":
        result = analytics.groupby_aggregate(
            df, intent.metric_col, intent.group_col, intent.func,
            top_n=intent.top_n, ascending=intent.ascending,
        )
        label = analytics.FA_FUNC_LABEL.get(intent.func, intent.func)
        top_row = result.iloc[0] if not result.empty else None
        rank_word = "کمترین" if intent.ascending else "بیشترین"
        if top_row is not None:
            answer = (
                f"{label} «{intent.metric_col}» به تفکیک «{intent.group_col}»: "
                f"{rank_word} مقدار مربوط به «{top_row[intent.group_col]}» با "
                f"{analytics._fmt(top_row[intent.metric_col])} است."
            )
        else:
            answer = "داده‌ای برای این گروه‌بندی پیدا نشد."
        return AskResponse(
            ok=True,
            intent=intent.kind,
            answer=answer,
            table=result.to_dict(orient="records"),
            chart={
                "type": "bar",
                "labels": [str(x) for x in result[intent.group_col].tolist()],
                "series": [{"name": label, "data": [float(x) for x in result[intent.metric_col].tolist()]}],
            },
        )

    if intent.kind == "explain_change":
        result = analytics.explain_change(df, intent.metric_col, intent.group_col, intent.date_col)
        if not result["ok"]:
            return AskResponse(ok=False, intent=intent.kind, answer=result["reason"])
        return AskResponse(
            ok=True,
            intent=intent.kind,
            answer=result["narrative"],
            table=result["breakdown"],
            chart=result["chart"],
        )

    if intent.kind == "trend":
        result = analytics.trend_by_period(df, intent.metric_col, intent.date_col, intent.func)
        label = analytics.FA_FUNC_LABEL.get(intent.func, intent.func)
        data = result["series"][0]["data"]
        if len(data) >= 2:
            change = data[-1] - data[0]
            direction = "رشد" if change > 0 else ("افت" if change < 0 else "ثبات")
            answer = (
                f"روند {label} «{intent.metric_col}» از {result['labels'][0]} تا {result['labels'][-1]}: "
                f"{direction} به میزان {analytics._fmt(abs(change))}."
            )
        else:
            answer = f"روند {label} «{intent.metric_col}» محاسبه شد."
        return AskResponse(ok=True, intent=intent.kind, answer=answer, chart=result)

    # fallback
    desc = analytics.describe(df)
    cols = "، ".join(desc["columns"])
    answer = (
        "متوجه نشدم دقیقاً کدام ستون یا سنجه مدنظرتان است. "
        f"ستون‌های موجود در این دیتاست: {cols}. "
        "می‌توانید مثلاً بپرسید «مجموع فروش به تفکیک محصول چقدر است؟» یا "
        "«چرا فروش کاهش پیدا کرد؟»."
    )
    return AskResponse(ok=False, intent="fallback", answer=answer)


# فرانت‌اند استاتیک (بدون build) را از همین بک‌اند سرو می‌کند تا نیازی به تنظیم
# آدرس/CORS جداگانه برای اجرای محلی نباشد. باید بعد از همه‌ی مسیرهای /api بیاید.
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
