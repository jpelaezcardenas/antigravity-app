from datetime import datetime, timezone
from typing import Any, Optional

from core.supabase_client import get_service_supabase


def get_auto_approval_metrics(tenant_id: str, days: int = 7) -> dict[str, Any]:
    supabase = get_service_supabase()
    result = (
        supabase.table("metrics_snapshots")
        .select(
            "snapshot_date,auto_approved_total,auto_approved_recurring,"
            "auto_approved_vendor,auto_approved_micro,false_positive_count"
        )
        .eq("tenant_id", tenant_id)
        .order("snapshot_date", desc=True)
        .limit(days)
        .execute()
    )
    rows = result.data or []
    total = sum(r["auto_approved_total"] for r in rows)
    return {
        "days": days,
        "total_auto_approved": total,
        "by_rule": {
            "recurring": sum(r["auto_approved_recurring"] for r in rows),
            "vendor": sum(r["auto_approved_vendor"] for r in rows),
            "micro": sum(r["auto_approved_micro"] for r in rows),
        },
        "false_positives": sum(r["false_positive_count"] for r in rows),
        "daily": [
            {
                "date": r["snapshot_date"],
                "approved": r["auto_approved_total"],
                "false_positives": r["false_positive_count"],
            }
            for r in rows
        ],
    }


def get_csv_ingestion_metrics(tenant_id: str, days: int = 7) -> dict[str, Any]:
    supabase = get_service_supabase()
    result = (
        supabase.table("metrics_snapshots")
        .select("snapshot_date,csv_batches_total,csv_rows_processed,csv_rows_error")
        .eq("tenant_id", tenant_id)
        .order("snapshot_date", desc=True)
        .limit(days)
        .execute()
    )
    rows = result.data or []
    return {
        "days": days,
        "batches": sum(r["csv_batches_total"] for r in rows),
        "rows_processed": sum(r["csv_rows_processed"] for r in rows),
        "rows_error": sum(r["csv_rows_error"] for r in rows),
        "daily": [
            {
                "date": r["snapshot_date"],
                "batches": r["csv_batches_total"],
                "rows_ok": r["csv_rows_processed"],
                "rows_err": r["csv_rows_error"],
            }
            for r in rows
        ],
    }


def get_queue_health(tenant_id: str) -> dict[str, Any]:
    supabase = get_service_supabase()
    result = (
        supabase.table("metrics_snapshots")
        .select("queue_pending_count,queue_avg_review_seconds")
        .eq("tenant_id", tenant_id)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )
    row = (result.data or [{}])[0]
    return {
        "pending": row.get("queue_pending_count", 0),
        "avg_review_seconds": row.get("queue_avg_review_seconds"),
    }


def get_top_vendors(tenant_id: str, limit: int = 10) -> list[dict[str, Any]]:
    supabase = get_service_supabase()
    result = (
        supabase.table("metrics_snapshots")
        .select("top_vendors")
        .eq("tenant_id", tenant_id)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )
    row = (result.data or [{}])[0]
    vendors = row.get("top_vendors") or []
    return vendors[:limit]


def compute_and_upsert_snapshot(tenant_id: str, date: Optional[str] = None) -> dict[str, Any]:
    """Compute today's metrics from source tables and upsert into metrics_snapshots."""
    supabase = get_service_supabase()
    today = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Auto-approval counts from approval_queue
    # rule_type lives in data JSONB (data->>'rule_type'), not a top-level column
    aq = (
        supabase.table("approval_queue")
        .select("id,action_type,status,data")
        .eq("tenant_id", tenant_id)
        .gte("created_at", f"{today}T00:00:00Z")
        .lt("created_at", f"{today}T23:59:59Z")
        .execute()
    )
    aq_rows = aq.data or []
    approved = [r for r in aq_rows if r.get("status") == "approved"]

    def _rule(r: dict) -> str:
        data = r.get("data") or {}
        return data.get("rule_type") or data.get("auto_approval_rule") or r.get("action_type") or ""

    auto_approved_recurring = sum(1 for r in approved if "recurring" in _rule(r))
    auto_approved_vendor = sum(1 for r in approved if "vendor" in _rule(r))
    auto_approved_micro = sum(1 for r in approved if "micro" in _rule(r))
    false_positive_count = sum(1 for r in aq_rows if r.get("status") == "rejected")
    queue_pending = sum(1 for r in aq_rows if r.get("status") == "pending")

    # CSV ingestion metrics from ingestion_batches (if table exists)
    try:
        ib = (
            supabase.table("ingestion_batches")
            .select("id,rows_ok,rows_error")
            .eq("tenant_id", tenant_id)
            .gte("created_at", f"{today}T00:00:00Z")
            .lt("created_at", f"{today}T23:59:59Z")
            .execute()
        )
        ib_rows = ib.data or []
    except Exception:
        ib_rows = []

    csv_batches = len(ib_rows)
    csv_rows_ok = sum(r.get("rows_ok", 0) for r in ib_rows)
    csv_rows_err = sum(r.get("rows_error", 0) for r in ib_rows)

    # Top vendors from erp_journal_lines
    try:
        vq = (
            supabase.table("erp_journal_lines")
            .select("description")
            .eq("tenant_id", tenant_id)
            .gte("entry_date", today)
            .execute()
        )
        from collections import Counter
        vendor_counts = Counter(
            r["description"] for r in (vq.data or []) if r.get("description")
        )
        top_vendors = [
            {"vendor": v, "count": c} for v, c in vendor_counts.most_common(10)
        ]
    except Exception:
        top_vendors = []

    snapshot = {
        "tenant_id": tenant_id,
        "snapshot_date": today,
        "auto_approved_total": len(approved),
        "auto_approved_recurring": auto_approved_recurring,
        "auto_approved_vendor": auto_approved_vendor,
        "auto_approved_micro": auto_approved_micro,
        "false_positive_count": false_positive_count,
        "csv_batches_total": csv_batches,
        "csv_rows_processed": csv_rows_ok,
        "csv_rows_error": csv_rows_err,
        "queue_pending_count": queue_pending,
        "top_vendors": top_vendors,
    }

    supabase.table("metrics_snapshots").upsert(
        snapshot,
        on_conflict="tenant_id,snapshot_date",
    ).execute()

    return snapshot
