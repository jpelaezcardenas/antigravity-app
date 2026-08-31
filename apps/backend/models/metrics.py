from datetime import date
from typing import Any

from pydantic import BaseModel


class DailyAutoApproval(BaseModel):
    date: date
    approved: int
    false_positives: int


class ByRule(BaseModel):
    recurring: int
    vendor: int
    micro: int


class AutoApprovalMetricsResponse(BaseModel):
    days: int
    total_auto_approved: int
    by_rule: ByRule
    false_positives: int
    daily: list[DailyAutoApproval]


class DailyCSVIngestion(BaseModel):
    date: date
    batches: int
    rows_ok: int
    rows_err: int


class CSVIngestionMetricsResponse(BaseModel):
    days: int
    batches: int
    rows_processed: int
    rows_error: int
    daily: list[DailyCSVIngestion]


class QueueHealthResponse(BaseModel):
    pending: int
    avg_review_seconds: float | None


class VendorEntry(BaseModel):
    vendor: str
    count: int


class SnapshotComputeResponse(BaseModel):
    tenant_id: str
    snapshot_date: str
    auto_approved_total: int
    false_positive_count: int
    csv_batches_total: int
    csv_rows_processed: int
    csv_rows_error: int
    queue_pending_count: int
    top_vendors: list[Any]
