"""مدیریت ذخیره و بازیابی دیتاست‌های آپلودشده (CSV/Excel).

MVP: ذخیره روی دیسک محلی (pickle + مانیفست JSON). برای production واقعی این لایه
باید با یک دیتابیس (Postgres/DuckDB) یا اتصال مستقیم به منبع داده (CRM، دیتابیس
شرکت) جایگزین شود؛ نگاه کنید به docs/ARCHITECTURE.md بخش «منابع داده».
"""
from __future__ import annotations

import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .storage import atomic_json, locked

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_PATH = DATA_DIR / "manifest.json"

MAX_ROWS = 200_000  # سقف امن برای پردازش در حافظه در MVP
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


class DatasetError(Exception):
    pass


def _load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_manifest(manifest: dict) -> None:
    atomic_json(MANIFEST_PATH, manifest)


def _read_tabular(filename: str, content: bytes) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    buf = io.BytesIO(content)
    if suffix in (".csv", ".tsv"):
        sep = "\t" if suffix == ".tsv" else None
        for encoding in ("utf-8-sig", "utf-8", "cp1256", "latin-1"):
            try:
                buf.seek(0)
                return pd.read_csv(buf, sep=sep, engine="python", encoding=encoding)
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        raise DatasetError("خواندن فایل CSV ممکن نشد؛ انکودینگ فایل را بررسی کنید.")
    if suffix in (".xlsx", ".xls"):
        try:
            return pd.read_excel(buf)
        except Exception as exc:  # noqa: BLE001
            raise DatasetError("خواندن فایل اکسل ممکن نشد؛ قالب و سلامت فایل را بررسی کنید.") from exc
    raise DatasetError("فرمت فایل پشتیبانی نمی‌شود. فقط CSV یا Excel (xlsx) مجاز است.")


def save_upload(filename: str, content: bytes) -> dict:
    if len(content) > MAX_FILE_SIZE:
        raise DatasetError("حجم فایل بیش از سقف مجاز (۲۵ مگابایت) است.")

    df = _read_tabular(filename, content)
    if df.empty:
        raise DatasetError("فایل خالی است یا هیچ سطر معتبری ندارد.")
    original_rows = len(df)
    if df.shape[0] > MAX_ROWS:
        df = df.head(MAX_ROWS)

    names = []
    used = set()
    for column in df.columns:
        base = str(column).strip() or "ستون"
        name = base
        suffix = 2
        while name in used:
            name = f"{base}_{suffix}"
            suffix += 1
        used.add(name)
        names.append(name)
    df.columns = names

    dataset_id = uuid.uuid4().hex[:12]
    store_path = DATA_DIR / f"{dataset_id}.pkl"
    df.to_pickle(store_path)

    meta = {
        "id": dataset_id,
        "name": filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "rows": int(df.shape[0]),
        "columns": list(df.columns),
        "original_rows": original_rows,
        "truncated": original_rows > MAX_ROWS,
    }

    with locked(MANIFEST_PATH):
        manifest = _load_manifest()
        manifest[dataset_id] = meta
        _save_manifest(manifest)
    return meta


def list_datasets() -> list[dict]:
    manifest = _load_manifest()
    return sorted(manifest.values(), key=lambda m: m["uploaded_at"], reverse=True)


def get_meta(dataset_id: str) -> dict | None:
    return _load_manifest().get(dataset_id)


def load_dataframe(dataset_id: str) -> pd.DataFrame:
    meta = get_meta(dataset_id)
    if not meta:
        raise DatasetError("دیتاست پیدا نشد.")
    store_path = DATA_DIR / f"{dataset_id}.pkl"
    if not store_path.exists():
        raise DatasetError("فایل ذخیره‌شده‌ی دیتاست در دسترس نیست.")
    return pd.read_pickle(store_path)


def delete_dataset(dataset_id: str) -> None:
    with locked(MANIFEST_PATH):
        manifest = _load_manifest()
        if dataset_id not in manifest:
            raise DatasetError("دیتاست پیدا نشد.")
        del manifest[dataset_id]
        _save_manifest(manifest)
    store_path = DATA_DIR / f"{dataset_id}.pkl"
    if store_path.exists():
        store_path.unlink()
