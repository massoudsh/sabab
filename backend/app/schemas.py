from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class DatasetMeta(BaseModel):
    id: str
    name: str
    uploaded_at: str
    rows: int
    columns: list[str]


class DatasetDetail(DatasetMeta):
    preview: list[dict[str, Any]]
    numeric_columns: list[str]
    date_columns: list[str]


class AskRequest(BaseModel):
    dataset_id: str
    question: str


class ChartSeries(BaseModel):
    name: str
    data: list[float]


class ChartData(BaseModel):
    type: str
    labels: list[str]
    series: list[ChartSeries]


class AskResponse(BaseModel):
    ok: bool
    intent: str
    answer: str
    table: Optional[list[dict[str, Any]]] = None
    chart: Optional[ChartData] = None
