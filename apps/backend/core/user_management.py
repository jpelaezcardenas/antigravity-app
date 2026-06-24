"""
User Management Service
Phase 3B: Customer Onboarding System

Handles:
- Customer invitations + self-registration
- Team member invitations + auto-onboarding
- Role management
- User offboarding
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
import secrets
import logging

logger = logging.getLogger(__name__)


class CustomerInviteService:
    """Manage customer (tenant) invitations and registration."""

    @staticmethod
    async def create_invite(
        creator_id: str,
        customer_name: str,
        customer_email: str,
        plan: str,  # starter, pro, enterprise
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Create customer invitation.

        Called by: Contexia admin (Juan David)
        Creates: customer_invites record with 7-day expiration

        Args:
            creator_id: UUID of admin creating invite (e.g., Juan David)
            customer_name: Name of customer company
            customer_email: Email of customer admin
            plan: Plan type (starter, pro, enterprise)
            session: Database session

        Returns:
            {
                "invite_id": uuid,
                "invite_link": "https://contexia.online/onboard?token=...",
                "expires_at": datetime,
                "plan": plan
            }
        """
        from main import db

        # Generate invite token
        invite_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)

        # Insert invite
        stmt = db.customer_invites.insert().values(
            created_by=creator_id,
            customer_name=customer_name,
            customer_email=customer_email,
            plan=plan,
            invite_token=invite_token,
            invite_expires_at=expires_at,
            status='pending',
            created_at=datetime.utcnow()
        )

        result = await session.execute(stmt)
        await session.commit()

        invite_id = result.inserted_primary_key[0]

        logger.info(f"Created customer invite {invite_id} for {customer_email}")

        return {
            "invite_id": invite_id,
            "invite_link": f"https://contexia.online/onboard?token={invite_token}",
            "expires_at": expires_at,
            "plan": plan,
            "customer_email": customer_email
        }

    @staticmethod
    async def validate_invite_token(
        invite_token: str,
        session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Validate invite token and check expiration.

        Returns: customer_invite record if valid, None if invalid/expired

        Called by: register_customer Hermes operator
        """
        from main import db

        query = select(db.customer_invites).where(
            and_(
                db.customer_invites.c.invite_token == invite_token,
                db.customer_invites.c.status == 'pending'
            )
        )

        result = await session.execute(query)
        invite = result.one_or_none()

        if not invite:
            logger.warning(f"Invalid or expired invite token")
            return None

        # Check expiration
        if datetime.utcnow() > invite['invite_expires_at']:
            # Mark as expired
            await session.execute(
                update(db.customer_invites)
                .where(db.customer_invites.c.id == invite['id'])
                .values(status='expired')
            )
            await session.commit()
            logger.warning(f"Invite {invite['id']} expired")
            return None

        return dict(invite)

    @staticmethod
    async def mark_invite_accepted(
        invite_id: str,
        tenant_id: str,
        operator_id: str,
        session: AsyncSession
    ) -> None:
        """
        Mark invite as accepted after successful registration.

        Called by: register_customer Hermes operator
        """
        from main import db

        await session.execute(
            update(db.customer_invites)
            .where(db.customer_invites.c.id == invite_id)
            .values(
                status='accepted',
                accepted_at=datetime.utcnow(),
                created_tenant_id=tenant_id,
                operator_id=operator_id,
                operator_executed_at=datetime.utcnow()
            )
        )
        await session.commit()
        logger.info(f"Marked invite {invite_id} as accepted (tenant {tenant_id})")


class TeamInviteService:
    """Manage team member invitations and onboarding."""

    @staticmethod
    async def create_invite(
        tenant_id: str,
        invited_by_id: str,
        invitee_email: str,
        role: str,  # admin, finance, marketing, growth, operator, viewer
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Create team member invitation.

        Called by: Customer admin or Contexia admin
        Creates: team_invites record with 7-day expiration

        Args:
            tenant_id: UUID of tenant (customer)
            invited_by_id: UUID of user creating invite
            invitee_email: Email of team member to invite
            role: Role to assign
            session: Database session

        Returns:
            {
                "invite_id": uuid,
                "invite_link": "https://contexia.online/onboard?token=...",
                "expires_at": datetime,
                "role": role
            }
        """
        from main import db

        # Generate invite token
        invite_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)

        # Insert invite
        stmt = db.team_invites.insert().values(
            tenant_id=tenant_id,
            invited_by=invited_by_id,
            invitee_email=invitee_email,
            role=role,
            invite_token=invite_token,
            invite_expires_at=expires_at,
            status='pending',
            created_at=datetime.utcnow()
        )

        result = await session.execute(stmt)
        await session.commit()

        invite_id = result.inserted_primary_key[0]

        logger.info(f"Created team invite {invite_id} for {invitee_email} (role={role})")

        return {
            "invite_id": invite_id,
            "invite_link": f"https://contexia.online/onboard?token={invite_token}",
            "expires_at": expires_at,
            "role": role,
            "invitee_email": invitee_email
        }

    @staticmethod
    async def validate_invite_token(
        invite_token: str,
        session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Validate team invite token and check expiration.

        Called by: onboard_team_member Hermes operator
        """
        from main import db

        query = select(db.team_invites).where(
            and_(
                db.team_invites.c.invite_token == invite_token,
                db.team_invites.c.status == 'pending'
            )
        )

        result = await session.execute(query)
        invite = result.one_or_none()

        if not invite:
            logger.warning(f"Invalid or expired team invite token")
            return None

        # Check expiration
        if datetime.utcnow() > invite['invite_expires_at']:
            # Mark as expired
            await session.execute(
                update(db.team_invites)
                .where(db.team_invites.c.id == invite['id'])
                .values(status='expired')
            )
            await session.commit()
            logger.warning(f"Team invite {invite['id']} expired")
            return None

        return dict(invite)

    @staticmethod
    async def mark_invite_accepted(
        invite_id: str,
        user_id: str,
        operator_id: str,
        session: AsyncSession
    ) -> None:
        """
        Mark invite as accepted after successful onboarding.

        Called by: onboard_team_member Hermes operator
        """
        from main import db

        await session.execute(
            update(db.team_invites)
            .where(db.team_invites.c.id == invite_id)
            .values(
                status='accepted',
                accepted_at=datetime.utcnow(),
                created_user_id=user_id,
                operator_id=operator_id,
                operator_executed_at=datetime.utcnow()
            )
        )
        await session.commit()
        logger.info(f"Marked team invite {invite_id} as accepted (user {user_id})")


class OnboardingWorkflowService:
    """Audit trail for all onboarding operations."""

    @staticmethod
    async def log_workflow(
        tenant_id: str,
        workflow_type: str,  # customer_registration, team_onboarding, role_update, etc.
        operator_id: str,
        user_id: Optional[str],
        role_assigned: Optional[str],
        status: str,  # pending, in_progress, completed, failed
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Log onboarding workflow for audit trail.

        Called by: Hermes operators to log what they're doing

        Args:
            tenant_id: UUID of customer tenant
            workflow_type: Type of workflow (customer_registration, team_onboarding, etc.)
            operator_id: Name of Hermes operator
            user_id: UUID of user being affected (optional)
            role_assigned: Role being assigned (optional)
            status: Current status (pending, in_progress, completed, failed)
            error_message: Error message if failed (optional)
            metadata: Additional context (optional)
            session: Database session

        Returns:
            Workflow record
        """
        from main import db

        stmt = db.onboarding_workflows.insert().values(
            tenant_id=tenant_id,
            workflow_type=workflow_type,
            operator_id=operator_id,
            user_id=user_id,
            role_assigned=role_assigned,
            status=status,
            error_message=error_message,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )

        result = await session.execute(stmt)
        await session.commit()

        workflow_id = result.inserted_primary_key[0]

        logger.info(
            f"Logged workflow {workflow_id}: {workflow_type} "
            f"(operator={operator_id}, status={status})"
        )

        return {
            "workflow_id": workflow_id,
            "tenant_id": tenant_id,
            "workflow_type": workflow_type,
            "operator_id": operator_id,
            "status": status
        }

    @staticmethod
    async def update_workflow_status(
        workflow_id: str,
        status: str,
        error_message: Optional[str] = None,
        session: AsyncSession = None
    ) -> None:
        """
        Update workflow status (e.g., pending → in_progress → completed).

        Called by: Hermes operators to update progress
        """
        from main import db

        update_values = {
            "status": status,
            db.onboarding_workflows.c.completed_at: datetime.utcnow() if status == 'completed' else None
        }

        if status == 'in_progress':
            update_values[db.onboarding_workflows.c.started_at] = datetime.utcnow()

        if error_message:
            update_values["error_message"] = error_message

        await session.execute(
            update(db.onboarding_workflows)
            .where(db.onboarding_workflows.c.id == workflow_id)
            .values(**update_values)
        )
        await session.commit()

        logger.info(f"Updated workflow {workflow_id} status → {status}")
