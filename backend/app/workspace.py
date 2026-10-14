from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "workspace.json"


def _load() -> dict[str, list[dict[str, Any]]]:
    if not STORE_PATH.exists():
        return {"connections": [], "dashboards": [], "alerts": [], "comments": []}
    with STORE_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return {key: data.get(key, []) for key in ("connections", "dashboards", "alerts", "comments")}


def _save(data: dict[str, list[dict[str, Any]]]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STORE_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _new_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {"id": uuid.uuid4().hex[:12], "created_at": datetime.now(timezone.utc).isoformat(), **payload}


def list_records(kind: str) -> list[dict[str, Any]]:
    return _load()[kind]


def add_record(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = _load()
    record = _new_record(payload)
    data[kind].insert(0, record)
    _save(data)
    return record


def update_record(kind: str, record_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    data = _load()
    for record in data[kind]:
        if record["id"] == record_id:
            record.update(updates)
            _save(data)
            return record
    return None


def delete_record(kind: str, record_id: str) -> bool:
    data = _load()
    original = len(data[kind])
    data[kind] = [record for record in data[kind] if record["id"] != record_id]
    if len(data[kind]) == original:
        return False
    _save(data)
    return True
