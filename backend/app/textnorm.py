"""نرمال‌سازی متن فارسی برای تطبیق سؤال کاربر با نام ستون‌ها و کلیدواژه‌ها."""
import re

_AR_TO_FA = str.maketrans({
    "ي": "ی",
    "ك": "ک",
    "ة": "ه",
    "ۀ": "ه",
    "إ": "ا",
    "أ": "ا",
    "آ": "ا",
    "ؤ": "و",
    "ئ": "ی",
})

_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED]")
_PUNCT = re.compile(r"[؟?!.,،؛:\"'“”«»()\[\]{}/\\]")
_MULTI_SPACE = re.compile(r"\s+")

_FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_DIGIT_MAP = str.maketrans(
    _FA_DIGITS + _AR_DIGITS,
    "01234567890123456789",
)


def normalize(text: str) -> str:
    if text is None:
        return ""
    t = str(text).strip()
    t = t.translate(_AR_TO_FA)
    t = t.translate(_DIGIT_MAP)
    t = _DIACRITICS.sub("", t)
    t = _PUNCT.sub(" ", t)
    t = t.replace("‌", " ")  # نیم‌فاصله -> فاصله برای تطبیق ساده‌تر
    t = _MULTI_SPACE.sub(" ", t)
    return t.strip().lower()


def tokens(text: str) -> list[str]:
    return normalize(text).split()
