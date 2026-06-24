"""Tests for T11.2-T11.5: Swarm operators."""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime

from apps.backend.operators.swarm import (
    SwarmOperator,
    TaskResult,
    AuthOperator,
    DBOperator,
    RolesOperator,
    CommsOperator,
    WorkflowTrackerOperator,
)
from apps.backend.operators.conductor import Task, TaskStatus


class TestAuthOperator:
    """T11.2: Auth Operator"""

    @pytest.mark.asyncio
    async def test_create_auth_user(self):
        """Test creating Supabase auth user"""
        operator = AuthOperator()

        task = Task(
            id=str(uuid4()),
            type="create_auth_user",
            operator="auth_operator",
            payload={"invite_id": "test-invite", "email": "customer@example.com"},
        )

        result = await operator.execute(task)

        assert result.success
        assert result.operator == "auth_operator"
        assert result.cost > 0
        assert result.duration_ms > 0
        assert "user_id" in result.proof
        assert result.proof["email"] == "customer@example.com"

    @pytest.mark.asyncio
    async def test_auth_operator_cost(self):
        """Test that auth_create costs $0.001"""
        operator = AuthOperator()
        task = Task(
            id=str(uuid4()),
            type="create_auth_user",
            operator="auth_operator",
            payload={"invite_id": "test", "email": "test@example.com"},
        )

        result = await operator.execute(task)

        assert result.cost == 0.001


class TestDBOperator:
    """T11.3: DB Operator"""

    @pytest.mark.asyncio
    async def test_create_tenant(self):
        """Test creating tenant + user records"""
        operator = DBOperator()

        task = Task(
            id=str(uuid4()),
            type="create_tenant",
            operator="db_operator",
            payload={"customer_email": "customer@example.com", "plan": "pro"},
        )

        result = await operator.execute(task)

        assert result.success
        assert result.operator == "db_operator"
        assert result.cost > 0
        assert "tenant_id" in result.proof
        assert result.proof["plan"] == "pro"

    @pytest.mark.asyncio
    async def test_db_operator_cost(self):
        """Test that db_write_tenant costs $0.002"""
        operator = DBOperator()
        task = Task(
            id=str(uuid4()),
            type="create_tenant",
            operator="db_operator",
            payload={"customer_email": "test@example.com", "plan": "starter"},
        )

        result = await operator.execute(task)

        assert result.cost == 0.002


class TestRolesOperator:
    """T11.4: Roles Operator"""

    @pytest.mark.asyncio
    async def test_assign_admin_role(self):
        """Test assigning admin role"""
        operator = RolesOperator()

        task = Task(
            id=str(uuid4()),
            type="assign_admin_role",
            operator="roles_operator",
            payload={"email": "customer@example.com"},
        )

        result = await operator.execute(task)

        assert result.success
        assert result.operator == "roles_operator"
        assert result.proof["role"] == "admin"
        assert result.proof["assigned"] is True

    @pytest.mark.asyncio
    async def test_roles_operator_cost(self):
        """Test that db_write_role costs $0.0005"""
        operator = RolesOperator()
        task = Task(
            id=str(uuid4()),
            type="assign_admin_role",
            operator="roles_operator",
            payload={"email": "test@example.com"},
        )

        result = await operator.execute(task)

        assert result.cost == 0.0005


class TestCommsOperator:
    """T11.5: Comms Operator"""

    @pytest.mark.asyncio
    async def test_send_welcome_email(self):
        """Test sending welcome email"""
        operator = CommsOperator()

        task = Task(
            id=str(uuid4()),
            type="send_welcome_email",
            operator="comms_operator",
            payload={"email": "customer@example.com", "plan": "pro"},
        )

        result = await operator.execute(task)

        assert result.success
        assert result.operator == "comms_operator"
        assert result.proof["status"] == "sent"
        assert result.proof["email"] == "customer@example.com"

    @pytest.mark.asyncio
    async def test_comms_operator_cost(self):
        """Test that email_send costs $0.01"""
        operator = CommsOperator()
        task = Task(
            id=str(uuid4()),
            type="send_welcome_email",
            operator="comms_operator",
            payload={"email": "test@example.com", "plan": "starter"},
        )

        result = await operator.execute(task)

        assert result.cost == 0.01


class TestWorkflowTrackerOperator:
    """T11.5: Workflow Tracker Operator"""

    @pytest.mark.asyncio
    async def test_log_workflow(self):
        """Test logging workflow"""
        operator = WorkflowTrackerOperator()

        task = Task(
            id=str(uuid4()),
            type="log_workflow",
            operator="workflow_operator",
            payload={"mission_id": "mission-xyz", "email": "customer@example.com"},
        )

        result = await operator.execute(task)

        assert result.success
        assert result.operator == "workflow_operator"
        assert result.proof["logged"] is True
        assert result.proof["mission_id"] == "mission-xyz"

    @pytest.mark.asyncio
    async def test_workflow_operator_cost(self):
        """Test that workflow_log costs $0.0002"""
        operator = WorkflowTrackerOperator()
        task = Task(
            id=str(uuid4()),
            type="log_workflow",
            operator="workflow_operator",
            payload={"mission_id": "m-1", "email": "test@example.com"},
        )

        result = await operator.execute(task)

        assert result.cost == 0.0002


class TestParallelExecution:
    """Test parallel execution of multiple operators"""

    @pytest.mark.asyncio
    async def test_all_operators_execute_in_parallel(self):
        """Test that all operators can execute concurrently"""
        operators = {
            "auth": AuthOperator(),
            "db": DBOperator(),
            "roles": RolesOperator(),
            "comms": CommsOperator(),
            "workflow": WorkflowTrackerOperator(),
        }

        tasks = [
            Task(
                id=str(uuid4()),
                type="create_auth_user",
                operator="auth_operator",
                payload={"invite_id": "inv-1", "email": "test1@example.com"},
            ),
            Task(
                id=str(uuid4()),
                type="create_tenant",
                operator="db_operator",
                payload={"customer_email": "test2@example.com", "plan": "pro"},
            ),
            Task(
                id=str(uuid4()),
                type="assign_admin_role",
                operator="roles_operator",
                payload={"email": "test3@example.com"},
            ),
            Task(
                id=str(uuid4()),
                type="send_welcome_email",
                operator="comms_operator",
                payload={"email": "test4@example.com", "plan": "starter"},
            ),
            Task(
                id=str(uuid4()),
                type="log_workflow",
                operator="workflow_operator",
                payload={"mission_id": "m-1", "email": "test5@example.com"},
            ),
        ]

        # Execute all in parallel
        results = await asyncio.gather(
            operators["auth"].execute(tasks[0]),
            operators["db"].execute(tasks[1]),
            operators["roles"].execute(tasks[2]),
            operators["comms"].execute(tasks[3]),
            operators["workflow"].execute(tasks[4]),
        )

        assert len(results) == 5
        assert all(r.success for r in results)

        # Verify costs
        cost_map = {r.operator: r.cost for r in results}
        assert cost_map["auth_operator"] == 0.001
        assert cost_map["db_operator"] == 0.002
        assert cost_map["roles_operator"] == 0.0005
        assert cost_map["comms_operator"] == 0.01
        assert cost_map["workflow_operator"] == 0.0002

        # Total cost
        total_cost = sum(r.cost for r in results)
        assert total_cost == pytest.approx(0.0135)


class TestTaskResult:
    """Test TaskResult dataclass"""

    def test_task_result_success(self):
        """Test successful task result"""
        result = TaskResult(
            task_id="task-1",
            operator="auth_operator",
            success=True,
            proof={"user_id": "uuid-123"},
            cost=0.001,
            duration_ms=100,
        )

        assert result.success
        assert result.operator == "auth_operator"
        assert "user_id" in result.proof
        assert result.error is None

    def test_task_result_failure(self):
        """Test failed task result"""
        result = TaskResult(
            task_id="task-1",
            operator="auth_operator",
            success=False,
            proof={},
            cost=0.0,
            duration_ms=50,
            error="Auth service unavailable",
        )

        assert not result.success
        assert result.error == "Auth service unavailable"
