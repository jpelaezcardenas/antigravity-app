"""
Mission data models - Hermes-compatible mission tracking.

Provides models for:
- Mission (orchestrated work unit)
- Task (individual work item)
- Checkpoint (proof of completion)
- CostTracker (financial tracking)
"""

from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class MissionStatusEnum(str, Enum):
    """Mission states"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskStatusEnum(str, Enum):
    """Task states (Hermes Kanban compatible)"""
    ASSIGNED = "assigned"
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    TIMED_OUT = "timed_out"


class CheckpointStatusEnum(str, Enum):
    """Checkpoint states"""
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"


# ============================================================================
# DATABASE MODELS
# ============================================================================

class MissionModel(Base):
    """
    Mission table - Hermes-compatible orchestrated work units.

    Stores mission state, tasks, checkpoints, and cost tracking.
    """
    __tablename__ = "missions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Mission metadata
    type = Column(String(100), nullable=False)  # customer_registration, team_onboarding, etc
    status = Column(SQLEnum(MissionStatusEnum), nullable=False, default=MissionStatusEnum.PENDING)
    objective = Column(String(500), nullable=False)

    # Tenant isolation (Phase 1 multi-tenant)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)  # Optional: link to customer tenant

    # Progress tracking
    progress = Column(Float, nullable=False, default=0.0)  # 0-100%

    # Cost tracking
    cost = Column(Float, nullable=False, default=0.0)
    cost_breakdown = Column(JSON, nullable=True, default={})  # {"operator_name": cost}

    # Timing
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Blockers (tracking what's stuck)
    blockers = Column(JSON, nullable=True, default=[])  # List of blocker strings

    # Metadata
    metadata = Column(JSON, nullable=True)  # Arbitrary additional data

    # Indexes for performance
    __table_args__ = (
        Index("ix_missions_tenant_id", "tenant_id"),
        Index("ix_missions_status", "status"),
        Index("ix_missions_created_at", "created_at"),
    )


class TaskModel(Base):
    """
    Task table - Individual work items dispatched to operators.

    References Mission and tracks execution state.
    """
    __tablename__ = "tasks"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to mission
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"), nullable=False)

    # Task metadata
    type = Column(String(100), nullable=False)  # create_auth_user, create_tenant, etc
    operator = Column(String(100), nullable=False)  # auth_operator, db_operator, etc
    status = Column(SQLEnum(TaskStatusEnum), nullable=False, default=TaskStatusEnum.ASSIGNED)

    # Payload (task input)
    payload = Column(JSON, nullable=False, default={})

    # Result (task output)
    result = Column(JSON, nullable=True)  # TaskResult serialized

    # Timing
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Float, nullable=True)

    # Cost
    cost = Column(Float, nullable=False, default=0.0)

    # Indexes
    __table_args__ = (
        Index("ix_tasks_mission_id", "mission_id"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_operator", "operator"),
    )


class CheckpointModel(Base):
    """
    Checkpoint table - Proof of task completion.

    Records what each operator produced (user_id, tenant_id, role, email status, etc).
    """
    __tablename__ = "checkpoints"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to mission
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"), nullable=False)

    # Foreign key to task
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)

    # Checkpoint metadata
    task_type = Column(String(100), nullable=False)  # create_auth_user, etc
    operator_id = Column(String(100), nullable=False)  # auth_operator, etc
    status = Column(SQLEnum(CheckpointStatusEnum), nullable=False)

    # Proof (the actual result)
    proof = Column(JSON, nullable=False, default={})  # {"user_id": "...", "tenant_id": "..."}

    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    duration_ms = Column(Float, nullable=False, default=0.0)

    # Cost
    cost = Column(Float, nullable=False, default=0.0)

    # Indexes
    __table_args__ = (
        Index("ix_checkpoints_mission_id", "mission_id"),
        Index("ix_checkpoints_task_id", "task_id"),
        Index("ix_checkpoints_status", "status"),
    )


class CostTrackingModel(Base):
    """
    Cost tracking table - Financial visibility per operation.

    Tracks cost per operation type and mission for billing/analytics.
    """
    __tablename__ = "cost_tracking"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to mission (optional - can track costs outside missions)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"), nullable=True)

    # Operation details
    operation_type = Column(String(100), nullable=False)  # auth_create, db_write, email_send, etc
    operator = Column(String(100), nullable=False)  # auth_operator, comms_operator, etc

    # Cost
    cost = Column(Float, nullable=False)

    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional context (e.g., {"user_count": 1, "email_type": "welcome"})

    # Tenant isolation
    tenant_id = Column(UUID(as_uuid=True), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Indexes
    __table_args__ = (
        Index("ix_cost_tracking_mission_id", "mission_id"),
        Index("ix_cost_tracking_operation", "operation_type"),
        Index("ix_cost_tracking_created_at", "created_at"),
    )


# ============================================================================
# COST TRACKER UTILITY
# ============================================================================

class CostTracker:
    """
    Utility for tracking operation costs.

    Different operations have different costs:
    - Supabase auth user: $0.001
    - DB write (tenant): $0.002
    - DB write (user): $0.0005 each
    - Email send: $0.01
    - RLS policy check: $0.0001
    """

    # Cost matrix
    OPERATION_COSTS = {
        "auth_create": 0.001,
        "db_write_tenant": 0.002,
        "db_write_user": 0.0005,
        "db_write_role": 0.0005,
        "email_send": 0.01,
        "rls_check": 0.0001,
        "workflow_log": 0.0002,
    }

    @classmethod
    def get_cost(cls, operation_type: str) -> float:
        """Get cost for operation type"""
        return cls.OPERATION_COSTS.get(operation_type, 0.0)

    @classmethod
    def calculate_mission_cost(cls, operations: list) -> float:
        """Calculate total cost for mission (sum of all operations)"""
        return sum(cls.get_cost(op) for op in operations)

    @classmethod
    def breakdown_by_operator(cls, mission_cost_breakdown: dict) -> dict:
        """
        Format cost breakdown for display.

        Args:
            mission_cost_breakdown: {"auth_operator": 0.001, "db_operator": 0.002, ...}

        Returns:
            Formatted breakdown with totals
        """
        return {
            "by_operator": mission_cost_breakdown,
            "total": sum(mission_cost_breakdown.values()),
            "breakdown": f"${sum(mission_cost_breakdown.values()):.4f} total"
        }
