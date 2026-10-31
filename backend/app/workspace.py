from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .datastore import DATA_DIR
from .storage import atomic_json, locked

STORE_PATH = DATA_DIR / "workspace.json"
KINDS = ("connections", "dashboards", "alerts", "comments")


def _load() -> dict[str, list[dict[str, Any]]]:
    if not STORE_PATH.exists():
        return {key: [] for key in KINDS}
    with STORE_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return {key: data.get(key, []) for key in KINDS}


def list_records(kind: str) -> list[dict[str, Any]]:
    return _load()[kind]


def add_record(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    with locked(STORE_PATH):
        data = _load()
        record = {**payload, "id": uuid.uuid4().hex[:12], "created_at": datetime.now(timezone.utc).isoformat()}
        data[kind].insert(0, record)
        atomic_json(STORE_PATH, data)
        return record


def update_record(kind: str, record_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    with locked(STORE_PATH):
        data = _load()
        for record in data[kind]:
            if record["id"] == record_id:
                record.update(updates)
                atomic_json(STORE_PATH, data)
                return record
    return None


def delete_record(kind: str, record_id: str) -> bool:
    with locked(STORE_PATH):
        data = _load()
        original = len(data[kind])
        data[kind] = [record for record in data[kind] if record["id"] != record_id]
        if len(data[kind]) == original:
            return False
        atomic_json(STORE_PATH, data)
        return True


def delete_dataset_records(dataset_id: str) -> dict[str, int]:
    with locked(STORE_PATH):
        data = _load()
        removed = {}
        for kind in KINDS:
            original = len(data[kind])
            data[kind] = [record for record in data[kind] if record["dataset_id"] != dataset_id]
            removed[kind] = original - len(data[kind])
        atomic_json(STORE_PATH, data)
        return removed
