"""تشخیص و تبدیل تاریخ شمسی (جلالی) به میلادی برای ستون‌های تاریخ در داده‌های ایرانی.

pandas.Timestamp فقط سال‌های میلادی ۱۶۷۷ تا ۲۲۶۲ را پشتیبانی می‌کند، بنابراین
تاریخ‌هایی مثل «۱۴۰۳/۰۱/۰۵» (سال شمسی) باید قبل از استفاده در pandas به میلادی
تبدیل شوند؛ در غیر این صورت هرگز parse نمی‌شوند و کل تحلیل‌های زمانی می‌شکند.
"""
from __future__ import annotations

import re

import jdatetime
import pandas as pd

_FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_DIGIT_MAP = str.maketrans(_FA_DIGITS + _AR_DIGITS, "01234567890123456789")

# سال شمسی معتبر تقریباً بین ۱۲۰۰ تا ۱۵۰۰ برای داده‌های امروزی
_JALALI_PATTERN = re.compile(r"^(1[2-4]\d{2})[-/](\d{1,2})[-/](\d{1,2})")


def _to_ascii_digits(value) -> str:
    return str(value).translate(_DIGIT_MAP).strip()


def _convert_one(value):
    if pd.isna(value):
        return pd.NaT
    text = _to_ascii_digits(value)
    m = _JALALI_PATTERN.match(text)
    if not m:
        return pd.NaT
    year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        gregorian = jdatetime.date(year, month, day).togregorian()
        return pd.Timestamp(gregorian)
    except ValueError:
        return pd.NaT


def is_jalali_series(series: pd.Series, threshold: float = 0.7) -> bool:
    sample = series.dropna().astype(str).head(30)
    if sample.empty:
        return False
    matches = sample.apply(lambda v: bool(_JALALI_PATTERN.match(_to_ascii_digits(v))))
    return matches.mean() >= threshold


def parse_jalali_series(series: pd.Series) -> pd.Series:
    return series.apply(_convert_one)


def to_period_label(ts) -> str | None:
    """برچسب دوره‌ی ماهانه بر اساس تقویم شمسی (نه میلادی)، مثلاً «۱۴۰۳-۰۱».

    چون ماه‌های شمسی و میلادی هم‌مرز نیستند، گروه‌بندی زمانی برای کسب‌وکار ایرانی
    باید روی مرزهای واقعی ماه شمسی انجام شود، نه ماه میلادی.
    """
    if pd.isna(ts):
        return None
    jd = jdatetime.date.fromgregorian(date=pd.Timestamp(ts).date())
    return f"{jd.year:04d}-{jd.month:02d}"
