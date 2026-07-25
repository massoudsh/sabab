"""موتور تحلیل روی داده جدولی (pandas). بدون وابستگی به LLM خارجی."""
from __future__ import annotations

import pandas as pd
from typing import Optional

from . import jalali


AGG_FUNCS = {
    "sum": "sum",
    "mean": "mean",
    "max": "max",
    "min": "min",
    "count": "count",
}

FA_FUNC_LABEL = {
    "sum": "مجموع",
    "mean": "میانگین",
    "max": "بیشترین",
    "min": "کمترین",
    "count": "تعداد",
}


def detect_date_columns(df: pd.DataFrame) -> list[str]:
    result = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            result.append(col)
            continue
        if df[col].dtype == object:
            sample = df[col].dropna().head(20)
            if len(sample) == 0:
                continue
            if jalali.is_jalali_series(sample):
                result.append(col)
                continue
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.8:
                result.append(col)
    return result


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def categorical_columns(df: pd.DataFrame, date_cols: Optional[list[str]] = None) -> list[str]:
    date_cols = date_cols or []
    return [
        c for c in df.columns
        if c not in date_cols and not pd.api.types.is_numeric_dtype(df[c])
    ]


def as_datetime(df: pd.DataFrame, col: str) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(df[col]):
        return df[col]
    if jalali.is_jalali_series(df[col]):
        return jalali.parse_jalali_series(df[col])
    return pd.to_datetime(df[col], errors="coerce", format="mixed")


def aggregate_column(df: pd.DataFrame, column: str, func: str, filters: Optional[dict] = None):
    d = apply_filters(df, filters)
    series = d[column].dropna()
    if func == "count":
        return int(series.shape[0])
    value = getattr(series, func)()
    return None if pd.isna(value) else float(value)


def apply_filters(df: pd.DataFrame, filters: Optional[dict]) -> pd.DataFrame:
    if not filters:
        return df
    d = df
    for col, val in filters.items():
        if col in d.columns:
            d = d[d[col].astype(str).str.strip() == str(val).strip()]
    return d


def groupby_aggregate(
    df: pd.DataFrame,
    metric_col: str,
    group_col: str,
    func: str = "sum",
    top_n: Optional[int] = None,
    ascending: bool = False,
    filters: Optional[dict] = None,
) -> pd.DataFrame:
    d = apply_filters(df, filters)
    grouped = d.groupby(group_col, dropna=False)[metric_col].agg(func).reset_index()
    grouped.columns = [group_col, metric_col]
    grouped = grouped.sort_values(metric_col, ascending=ascending)
    if top_n:
        grouped = grouped.head(top_n)
    return grouped.reset_index(drop=True)


def explain_change(
    df: pd.DataFrame,
    metric_col: str,
    group_col: str,
    date_col: str,
) -> dict:
    """تجزیهٔ تغییر یک شاخص بین دو دورهٔ اخیر به تفکیک یک بُعد (مثلاً محصول/کانال/شهر).

    خروجی شامل روایت فارسی، جدول سهم هر دسته در تغییر، و داده‌ی نمودار است.
    """
    d = df.copy()
    d["__date__"] = as_datetime(d, date_col)
    d = d.dropna(subset=["__date__", metric_col])
    if d.empty:
        return {"ok": False, "reason": "داده‌ی معتبر تاریخ‌دار برای این تحلیل کافی نیست."}

    d["__period__"] = d["__date__"].apply(jalali.to_period_label)
    periods = sorted(d["__period__"].dropna().unique())
    if len(periods) < 2:
        return {"ok": False, "reason": "برای مقایسه‌ی روند حداقل به دو دوره‌ی زمانی متفاوت نیاز است."}

    prev_period, curr_period = periods[-2], periods[-1]

    prev = d[d["__period__"] == prev_period].groupby(group_col)[metric_col].sum()
    curr = d[d["__period__"] == curr_period].groupby(group_col)[metric_col].sum()

    combined = pd.DataFrame({"قبل": prev, "بعد": curr}).fillna(0)
    combined["تغییر"] = combined["بعد"] - combined["قبل"]
    combined = combined.sort_values("تغییر")

    total_prev = float(combined["قبل"].sum())
    total_curr = float(combined["بعد"].sum())
    total_delta = total_curr - total_prev
    pct = (total_delta / total_prev * 100) if total_prev else None

    direction = "افت" if total_delta < 0 else ("رشد" if total_delta > 0 else "بدون تغییر")

    biggest_drop = combined.iloc[0] if not combined.empty else None
    biggest_gain = combined.iloc[-1] if not combined.empty else None

    lines = []
    lines.append(
        f"مجموع «{metric_col}» از {_fmt(total_prev)} در {prev_period} به {_fmt(total_curr)} در {curr_period} رسید "
        f"({direction}: {_fmt(abs(total_delta))}"
        + (f"، معادل {pct:.1f}٪)" if pct is not None else ")")
    )
    if biggest_drop is not None and biggest_drop["تغییر"] < 0:
        lines.append(
            f"بیشترین افت مربوط به «{biggest_drop.name}» بود ({_fmt(biggest_drop['تغییر'])})."
        )
    if biggest_gain is not None and biggest_gain["تغییر"] > 0:
        lines.append(
            f"بیشترین رشد مربوط به «{biggest_gain.name}» بود (+{_fmt(biggest_gain['تغییر'])})."
        )

    table = combined.reset_index().rename(columns={group_col: group_col})
    table_records = table.to_dict(orient="records")

    return {
        "ok": True,
        "narrative": " ".join(lines),
        "prev_period": str(prev_period),
        "curr_period": str(curr_period),
        "total_prev": total_prev,
        "total_curr": total_curr,
        "total_delta": total_delta,
        "breakdown": table_records,
        "chart": {
            "type": "bar",
            "labels": [str(x) for x in table[group_col].tolist()],
            "series": [{"name": "تغییر", "data": [float(x) for x in table["تغییر"].tolist()]}],
        },
    }


def trend_by_period(df: pd.DataFrame, metric_col: str, date_col: str, func: str = "sum") -> dict:
    d = df.copy()
    d["__date__"] = as_datetime(d, date_col)
    d = d.dropna(subset=["__date__", metric_col])
    d["__period__"] = d["__date__"].apply(jalali.to_period_label)
    d = d.dropna(subset=["__period__"])
    grouped = d.groupby("__period__")[metric_col].agg(func).sort_index()
    return {
        "type": "line",
        "labels": [str(p) for p in grouped.index],
        "series": [{"name": FA_FUNC_LABEL.get(func, func), "data": [float(v) for v in grouped.values]}],
    }


def describe(df: pd.DataFrame) -> dict:
    return {
        "rows": int(df.shape[0]),
        "columns": list(df.columns),
        "numeric_columns": numeric_columns(df),
        "date_columns": detect_date_columns(df),
        "preview": df.head(5).fillna("").astype(str).to_dict(orient="records"),
    }


def _fmt(value: float) -> str:
    if value is None:
        return "-"
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}"
    return f"{value:,.2f}"
