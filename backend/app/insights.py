"""موتور بینش خودکار (Insight Engine).

برخلاف ``nlu.py`` که به یک سؤال مشخص کاربر جواب می‌دهد، این موتور بدون هیچ
سؤالی، مستقیم روی دیتافریم اجرا می‌شود و مهم‌ترین یافته‌ها را خودش پیدا می‌کند:
جهش/افت غیرعادی در یک دوره، تمرکز بیش‌ازحد یک دسته در یک سنجه، و دسته‌هایی
که به‌طور غیرعادی از میانگین بقیه فاصله دارند. خروجی این ماژول همان محصول
«چرا» را به سمت فاز ۴ نقشهٔ راه (docs/ARCHITECTURE.md بخش ۸: «هشدار پیش‌فعال»)
می‌برد، بدون نیاز به فراخوانی LLM خارجی — کاملاً قانون‌محور و رایگان، هم‌راستا
با فلسفهٔ ``nlu.py``.

خروجی هر بینش یک دیکشنری با کلیدهای ``type``, ``severity``, ``narrative``,
``metric_col``, ``group_col``, ``chart`` (اختیاری) است.
"""
from __future__ import annotations

import pandas as pd

from . import analytics

MAX_NUMERIC_COLS = 5
MAX_CATEGORICAL_COLS = 5
TREND_CHANGE_THRESHOLD = 0.2  # ۲۰٪ تغییر دوره‌به‌دوره برای فلگ شدن
CONCENTRATION_THRESHOLD = 0.5  # یک دسته بیش از ۵۰٪ کل را به خود اختصاص داده
OUTLIER_GROUP_Z = 2.0  # فاصلهٔ z-score یک گروه از میانگین گروه‌ها
DATA_QUALITY_MISSING_RATIO = 0.2  # بیش از ۲۰٪ مقدار خالی در یک ستون
MAX_INSIGHTS = 5


def generate_insights(df: pd.DataFrame) -> list[dict]:
    """مهم‌ترین یافته‌های خودکار روی یک دیتافریم را برمی‌گرداند (حداکثر MAX_INSIGHTS تا)."""
    if df.empty:
        return []

    date_cols = analytics.detect_date_columns(df)
    numeric_cols = analytics.numeric_columns(df)[:MAX_NUMERIC_COLS]
    categorical_cols = analytics.categorical_columns(df, date_cols)[:MAX_CATEGORICAL_COLS]

    candidates: list[tuple[float, dict]] = []

    candidates += _trend_insights(df, numeric_cols, date_cols)
    candidates += _concentration_insights(df, numeric_cols, categorical_cols)
    candidates += _outlier_group_insights(df, numeric_cols, categorical_cols)
    candidates += _data_quality_insights(df)

    candidates.sort(key=lambda pair: pair[0], reverse=True)
    return [insight for _, insight in candidates[:MAX_INSIGHTS]]


def _trend_insights(df, numeric_cols, date_cols) -> list[tuple[float, dict]]:
    if len(date_cols) != 1:
        return []
    date_col = date_cols[0]
    out = []
    for metric_col in numeric_cols:
        try:
            result = analytics.trend_by_period(df, metric_col, date_col, "sum")
        except Exception:  # noqa: BLE001 — دیتای نامعتبر را نادیده بگیر، کل موتور را نشکن
            continue
        data = result["series"][0]["data"]
        if len(data) < 2:
            continue
        prev, curr = data[-2], data[-1]
        if prev == 0:
            continue
        pct = (curr - prev) / abs(prev)
        if abs(pct) < TREND_CHANGE_THRESHOLD:
            continue
        direction = "افت" if pct < 0 else "رشد"
        narrative = (
            f"«{metric_col}» در آخرین دوره ({result['labels'][-1]}) نسبت به دورهٔ قبل "
            f"({result['labels'][-2]}) {direction} {abs(pct) * 100:.0f}٪ داشته "
            f"(از {analytics._fmt(prev)} به {analytics._fmt(curr)})."
        )
        out.append((
            abs(pct),
            {
                "type": "trend",
                "severity": "warning" if abs(pct) >= 0.4 else "info",
                "metric_col": metric_col,
                "group_col": None,
                "narrative": narrative,
                "chart": result,
            },
        ))
    return out


def _concentration_insights(df, numeric_cols, categorical_cols) -> list[tuple[float, dict]]:
    out = []
    for metric_col in numeric_cols:
        for group_col in categorical_cols:
            try:
                grouped = analytics.groupby_aggregate(df, metric_col, group_col, "sum")
            except Exception:  # noqa: BLE001
                continue
            if grouped.empty or len(grouped) < 2:
                continue
            total = grouped[metric_col].sum()
            if total == 0:
                continue
            top = grouped.iloc[0]
            share = float(top[metric_col]) / float(total)
            if share < CONCENTRATION_THRESHOLD:
                continue
            narrative = (
                f"«{top[group_col]}» به‌تنهایی {share * 100:.0f}٪ از مجموع «{metric_col}» "
                f"را به خود اختصاص داده — تمرکز بالا روی یک دسته، ریسک وابستگی را بررسی کن."
            )
            out.append((
                share,
                {
                    "type": "concentration",
                    "severity": "warning" if share >= 0.7 else "info",
                    "metric_col": metric_col,
                    "group_col": group_col,
                    "narrative": narrative,
                    "chart": {
                        "type": "bar",
                        "labels": [str(x) for x in grouped[group_col].tolist()],
                        "series": [{"name": metric_col, "data": [float(x) for x in grouped[metric_col].tolist()]}],
                    },
                },
            ))
    return out


def _outlier_group_insights(df, numeric_cols, categorical_cols) -> list[tuple[float, dict]]:
    out = []
    for metric_col in numeric_cols:
        for group_col in categorical_cols:
            try:
                grouped = df.groupby(group_col, dropna=False)[metric_col].mean().dropna()
            except Exception:  # noqa: BLE001
                continue
            if len(grouped) < 3:
                continue
            mean = grouped.mean()
            std = grouped.std()
            if not std or pd.isna(std) or std == 0:
                continue
            z_scores = (grouped - mean) / std
            idx = z_scores.abs().idxmax()
            z = z_scores.loc[idx]
            if abs(z) < OUTLIER_GROUP_Z:
                continue
            direction = "بالاتر" if z > 0 else "پایین‌تر"
            narrative = (
                f"میانگین «{metric_col}» برای «{idx}» به‌طور غیرعادی {direction} از بقیهٔ "
                f"دسته‌های «{group_col}» است ({analytics._fmt(float(grouped.loc[idx]))} در برابر "
                f"میانگین کلی {analytics._fmt(float(mean))})."
            )
            out.append((
                abs(float(z)),
                {
                    "type": "outlier_group",
                    "severity": "warning" if abs(z) >= 3 else "info",
                    "metric_col": metric_col,
                    "group_col": group_col,
                    "narrative": narrative,
                    "chart": None,
                },
            ))
    return out


def _data_quality_insights(df) -> list[tuple[float, dict]]:
    out = []
    n = len(df)
    if n == 0:
        return out
    for col in df.columns:
        missing_ratio = float(df[col].isna().mean())
        if missing_ratio < DATA_QUALITY_MISSING_RATIO:
            continue
        narrative = (
            f"ستون «{col}» حدود {missing_ratio * 100:.0f}٪ مقدار خالی دارد؛ نتایج تحلیل‌های "
            f"مرتبط با این ستون ممکن است دقیق نباشد."
        )
        out.append((
            missing_ratio * 0.5,  # وزن کمتر از insight های تحلیلی تا در اولویت غرق نشوند
            {
                "type": "data_quality",
                "severity": "warning" if missing_ratio >= 0.5 else "info",
                "metric_col": col,
                "group_col": None,
                "narrative": narrative,
                "chart": None,
            },
        ))
    return out
