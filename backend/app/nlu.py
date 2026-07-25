"""تحلیل سؤال فارسیِ کاربر و تبدیل آن به یک عملیات تحلیلی روی دیتافریم.

این ماژول یک موتور قانون‌محور (rule-based) است، نه یک LLM. برای MVP کافی است و
هزینه/تأخیر API خارجی ندارد. نقطهٔ اتصال LLM در آینده می‌تواند جایگزین یا مکمل
تابع ``parse_question`` شود (نگاه کنید به docs/ARCHITECTURE.md بخش «گام بعدی NLU»).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

import pandas as pd

from . import analytics
from .textnorm import normalize

FUNC_KEYWORDS = {
    "mean": ["میانگین", "متوسط"],
    "sum": ["مجموع", "جمع", "کل", "جمع کل"],
    "max": ["بیشترین", "حداکثر", "ماکزیمم", "بالاترین"],
    "min": ["کمترین", "حداقل", "مینیمم", "پایین ترین", "پایین‌ترین"],
    "count": ["تعداد", "چند تا", "چندتا"],
}

GROUP_TRIGGER = ["به تفکیک", "برحسب", "بر حسب", "در هر", "به ازای هر"]
EXPLAIN_TRIGGER_WHY = ["چرا"]
EXPLAIN_TRIGGER_CHANGE = ["افت", "کاهش", "رشد", "افزایش", "تغییر کرد", "تغییر"]
TREND_TRIGGER = ["روند", "طی زمان", "در طول زمان", "روند تغییر", "نوسان"]

TOP_N_PATTERN = re.compile(r"(\d+)\s*(تا|مورد|محصول|رده|نفر)?\s*(برتر|اول)?")


@dataclass
class ParsedIntent:
    kind: str  # aggregate | groupby | explain_change | trend | fallback
    metric_col: str | None = None
    group_col: str | None = None
    date_col: str | None = None
    func: str = "sum"
    top_n: int | None = None
    ascending: bool = False
    filters: dict = field(default_factory=dict)
    reason: str | None = None


def _find_best_column(norm_question: str, columns: list[str]) -> str | None:
    """ستونی که نامش (نرمال‌شده) در متن سؤال ظاهر شده را با بیشترین طول تطبیق برمی‌گرداند."""
    best = None
    best_len = 0
    for col in columns:
        norm_col = normalize(col)
        if not norm_col:
            continue
        if norm_col in norm_question and len(norm_col) > best_len:
            best = col
            best_len = len(norm_col)
    if best:
        return best
    # fallback: تطبیق فازی برای غلط‌های تایپی کوچک
    best_ratio = 0.0
    for col in columns:
        norm_col = normalize(col)
        for token_window in _sliding_windows(norm_question, len(norm_col.split())):
            ratio = SequenceMatcher(None, norm_col, token_window).ratio()
            if ratio > best_ratio and ratio > 0.82:
                best_ratio = ratio
                best = col
    return best


def _sliding_windows(text: str, size: int):
    tokens = text.split()
    size = max(size, 1)
    for i in range(len(tokens) - size + 1):
        yield " ".join(tokens[i : i + size])


def _detect_func(norm_question: str) -> str | None:
    for func, keywords in FUNC_KEYWORDS.items():
        for kw in keywords:
            if normalize(kw) in norm_question:
                return func
    return None


def _detect_top_n(norm_question: str) -> int | None:
    if "برتر" in norm_question or "اول" in norm_question:
        m = TOP_N_PATTERN.search(norm_question)
        if m and m.group(1):
            return int(m.group(1))
    return None


def parse_question(question: str, df: pd.DataFrame) -> ParsedIntent:
    norm_q = normalize(question)

    numeric_cols = analytics.numeric_columns(df)
    date_cols = analytics.detect_date_columns(df)
    categorical_cols = analytics.categorical_columns(df, date_cols)

    metric_col = _find_best_column(norm_q, numeric_cols)
    group_col = _find_best_column(norm_q, categorical_cols)
    date_col = _find_best_column(norm_q, date_cols) or (date_cols[0] if len(date_cols) == 1 else None)

    func = _detect_func(norm_q)
    top_n = _detect_top_n(norm_q)

    is_why = any(normalize(k) in norm_q for k in EXPLAIN_TRIGGER_WHY)
    is_change = any(normalize(k) in norm_q for k in EXPLAIN_TRIGGER_CHANGE)
    is_trend = any(normalize(k) in norm_q for k in TREND_TRIGGER)
    has_group_trigger = any(normalize(k) in norm_q for k in GROUP_TRIGGER)

    has_analytic_signal = bool(func or is_why or is_change or is_trend or has_group_trigger)
    if not metric_col and numeric_cols and has_analytic_signal:
        # فقط وقتی سؤال واقعاً نشانه‌ی تحلیلی دارد (مثل «میانگین چقدره؟») و یک
        # ستون عددی بیشتر وجود ندارد، همان را حدس بزن؛ در غیر این صورت به fallback برو.
        if len(numeric_cols) == 1:
            metric_col = numeric_cols[0]

    if is_why and is_change and metric_col and date_col:
        if not group_col:
            group_col = categorical_cols[0] if categorical_cols else None
        if group_col:
            return ParsedIntent(
                kind="explain_change",
                metric_col=metric_col,
                group_col=group_col,
                date_col=date_col,
            )

    if is_trend and metric_col and date_col:
        return ParsedIntent(
            kind="trend",
            metric_col=metric_col,
            date_col=date_col,
            func=func or "sum",
        )

    if group_col and metric_col:
        # «بیشترین/کمترین» در کنار یک بُعد گروه‌بندی معمولاً یعنی «مجموع کدام گروه
        # بیشتر/کمتر است»، نه «بزرگ‌ترین/کوچک‌ترین تک‌رکورد داخل گروه». بنابراین این
        # کلیدواژه‌ها فقط جهت مرتب‌سازی گروه‌ها را تعیین می‌کنند، نه تابع تجمیع را.
        if func in ("max", "min"):
            group_func = "sum"
            ascending = func == "min"
        else:
            group_func = func or ("count" if not numeric_cols else "sum")
            ascending = False
        return ParsedIntent(
            kind="groupby",
            metric_col=metric_col,
            group_col=group_col,
            func=group_func,
            top_n=top_n,
            ascending=ascending,
        )

    if metric_col:
        return ParsedIntent(
            kind="aggregate",
            metric_col=metric_col,
            func=func or "sum",
        )

    return ParsedIntent(
        kind="fallback",
        reason="نتوانستم ستون یا سنجه‌ی مرتبط با سؤال را در داده پیدا کنم.",
    )
