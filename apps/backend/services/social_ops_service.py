"""Core service for Social Content Ops acquisition workflows."""

from __future__ import annotations

import hashlib
import logging
import os
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from channels.telegram import normalize_telegram_update
from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)

SUPPORTED_CHANNELS = {"telegram", "facebook", "instagram", "tiktok", "linkedin"}

PIPELINE_STAGES = [
    ("nuevo", "Nuevo"),
    ("diagnosticado", "Diagnosticado"),
    ("auditoria_sombra", "Auditoria Sombra"),
    ("formalizacion", "Formalizacion"),
    ("activacion_fase2", "Activacion Fase 2"),
    ("escalado_entidad_a", "Escalado Entidad A"),
    ("cerrado", "Cerrado"),
]

ONBOARDING_STEPS = [
    ("s1_kickoff", "S1 Kick-off", "Agendar kick-off 45m y alinear expectativas CFO + Escudo Legal"),
    ("s1_credentials", "S1 Credenciales", "Capturar token DIAN, ERP (Siigo/Alegra), bancos y pasarelas (solo lectura)"),
    ("s1_data_agreements", "S1 Datos y consentimientos", "Tratamiento de datos y autorizacion consulta DIAN"),
    ("s2_tech_setup", "S2 Setup tecnico", "Provision tenant, n8n mail-watcher, webhooks DIAN (UBL 2.1)"),
    ("s2_historical_sync", "S2 Sync historico", "Ingesta hasta 30 meses y reconciliacion >=98% (rate limits Siigo)"),
    ("s2_qa_gate", "S2 QA tecnico", "Gate: APIs activas, latencia <2s, match debe/haber, test Centinela"),
    ("handoff_day14", "Dia 14 Handoff", "Transferencia: Entidad B entrega plomeria; Entidad A asume criterio fiscal"),
    ("s3_shadow_audit", "S3 Auditoria Sombra", "IA fuzzy matching PUC + revision Entidad A (<90% certeza)"),
    ("s3_risk_crosscheck", "S3 Cruces de riesgo", "Lista Clinton, proveedores ficticios, RUT vencidos"),
    ("day21_go_live", "Dia 21 Go-Live", "Encender Centinela Fiscal y emitir primer Pulso Diario"),
    ("post_adoption", "Post Go-Live", "Monitoreo adopcion (>=3 logins/7d) + check-in dia 28"),
]

MATURITY_ORDER = {
    "Informal": 1,
    "Semi-formal": 2,
    "Formal Operativa": 3,
    "Formal Escalable": 4,
}

PAIN_KEYWORDS = {
    "embargo": ["embargo", "embargaron", "bloqueo de cuenta", "cuenta bloqueada"],
    "multa_dian": ["multa", "sancion", "sanción", "requerimiento", "dian"],
    "rut": ["rut", "registro mercantil", "camara de comercio", "cámara de comercio"],
    "stripe": ["stripe", "paypal", "pasarela", "shopify", "dropshipping"],
    "costos": ["costos", "centro de costos", "margen", "rentabilidad"],
    "auditoria": ["auditoria", "auditoría", "auditoria sombra", "revision", "revisión"],
    "nomina": ["nomina", "nómina", "empleado", "contratista"],
    "proveedor_riesgo": ["lista clinton", "proveedor ficticio", "proveedor fachada"],
}

CALCOM_SHADOW_AUDIT_URL = os.getenv(
    "CALCOM_SHADOW_AUDIT_URL", "https://cal.com/contexia/auditoria-sombra"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).lower()


def _safe_channel(channel: str) -> str:
    clean = (channel or "").lower().strip()
    if clean not in SUPPORTED_CHANNELS:
        raise ValueError(f"Unsupported channel: {channel}")
    return clean


def _default_accounts() -> List[Dict[str, Any]]:
    telegram_ready = bool(os.getenv("TELEGRAM_BOT_TOKEN"))
    meta_ready = bool(os.getenv("META_ACCESS_TOKEN"))
    tiktok_ready = bool(os.getenv("TIKTOK_CLIENT_KEY"))
    linkedin_ready = bool(os.getenv("LINKEDIN_ACCESS_TOKEN"))

    return [
        {
            "id": "telegram-primary",
            "channel": "telegram",
            "display_name": "Telegram Zero-UI",
            "auth_status": "connected" if telegram_ready else "ready_for_token",
            "capability_status": {
                "inbound": True,
                "commands": True,
                "handoff": True,
                "publishing": False,
            },
            "notes": "Webhook existente extendido para comandos, diagnostico y handoff.",
        },
        {
            "id": "meta-facebook",
            "channel": "facebook",
            "display_name": "Facebook Page",
            "auth_status": "connected" if meta_ready else "pending_app_review",
            "capability_status": {
                "inbound": meta_ready,
                "private_replies": meta_ready,
                "publishing": meta_ready,
            },
            "notes": "Opera con Meta Graph API y permisos aprobados; no scraping.",
        },
        {
            "id": "meta-instagram",
            "channel": "instagram",
            "display_name": "Instagram Business",
            "auth_status": "connected" if meta_ready else "pending_app_review",
            "capability_status": {
                "inbound": meta_ready,
                "private_replies": meta_ready,
                "publishing": meta_ready,
            },
            "notes": "Comentarios, mensajes y private replies dependen de permisos Meta activos.",
        },
        {
            "id": "tiktok-business",
            "channel": "tiktok",
            "display_name": "TikTok Business",
            "auth_status": "connected" if tiktok_ready else "capability_gated",
            "capability_status": {
                "inbound": False,
                "publishing": tiktok_ready,
                "webhooks": tiktok_ready,
            },
            "notes": "Inbound de comentarios queda gated hasta aprobacion real de API.",
        },
        {
            "id": "linkedin-organization",
            "channel": "linkedin",
            "display_name": "LinkedIn Organization Page",
            "auth_status": "connected" if linkedin_ready else "pending_oauth",
            "capability_status": {
                "organization_posts": linkedin_ready,
                "organization_comments": linkedin_ready,
                "personal_profile": False,
            },
            "notes": "Disenado para pagina de empresa con permisos organization social.",
        },
    ]


class SocialOpsService:
    """Inbound acquisition, qualification, command drafting, and handoff engine."""

    def __init__(self) -> None:
        self.persist_supabase = os.getenv("SOCIAL_OPS_PERSIST_SUPABASE", "false").lower() in {
            "1",
            "true",
            "yes",
        }
        self.reset_memory(seed=True)

    def reset_memory(self, seed: bool = True) -> None:
        self.events: Dict[str, Dict[str, Any]] = {}
        self.event_index: Dict[Tuple[str, str], str] = {}
        self.leads: Dict[str, Dict[str, Any]] = {}
        self.lead_index: Dict[Tuple[str, str], str] = {}
        self.pipeline_events: List[Dict[str, Any]] = []
        self.agent_runs: List[Dict[str, Any]] = []
        self.command_drafts: Dict[str, Dict[str, Any]] = {}
        self.onboarding_workspaces: Dict[str, Dict[str, Any]] = {}
        self.onboarding_seed_drafts: Dict[str, Dict[str, Any]] = {}
        self.onboarding_intake_items: List[Dict[str, Any]] = []
        self.service_tickets: Dict[str, Dict[str, Any]] = {}
        self.service_ticket_index: Dict[Tuple[str, str], str] = {}
        self.service_ticket_comments: List[Dict[str, Any]] = []
        self.sales_drafts: Dict[str, Dict[str, Any]] = {}
        self.reply_drafts: Dict[str, Dict[str, Any]] = {}
        self.service_reply_drafts: Dict[str, Dict[str, Any]] = {}
        self.ideas: Dict[int, Dict[str, Any]] = {}
        self.metrics: List[Dict[str, Any]] = []
        self.publications: List[Dict[str, Any]] = []
        self.channel_accounts = _default_accounts()
        if seed:
            self._seed_demo()

    def get_inbox(
        self,
        limit: int = 50,
        channel: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        items = list(self.events.values())
        if channel:
            items = [event for event in items if event["channel"] == channel]
        if status:
            items = [event for event in items if event["status"] == status]
        items.sort(key=lambda item: item["received_at"], reverse=True)
        return {
            "items": deepcopy(items[:limit]),
            "total": len(items),
            "channels": deepcopy(self.channel_accounts),
        }

    def get_pipeline(self) -> Dict[str, Any]:
        columns = []
        for stage_id, label in PIPELINE_STAGES:
            stage_leads = [
                deepcopy(lead)
                for lead in self.leads.values()
                if lead.get("pipeline_stage") == stage_id
            ]
            stage_leads.sort(key=lambda lead: lead.get("last_event_at") or "", reverse=True)
            columns.append({"id": stage_id, "label": label, "leads": stage_leads})

        pending_approvals = [
            draft for draft in self.command_drafts.values() if draft["status"] == "pending_approval"
        ]
        high_risk = [
            lead
            for lead in self.leads.values()
            if lead.get("urgency") in {"high", "critical"}
            or lead.get("pipeline_stage") == "escalado_entidad_a"
        ]
        return {
            "columns": columns,
            "summary": {
                "total_leads": len(self.leads),
                "inbox_events": len(self.events),
                "pending_approvals": len(pending_approvals),
                "high_risk_leads": len(high_risk),
                "connected_channels": len(
                    [
                        account
                        for account in self.channel_accounts
                        if account.get("auth_status") == "connected"
                    ]
                ),
            },
            "recent_pipeline_events": deepcopy(self.pipeline_events[-20:]),
        }

    def get_integrations(self) -> Dict[str, Any]:
        return {
            "items": deepcopy(self.channel_accounts),
            "policy": {
                "whatsapp_enabled": False,
                "sensitive_actions": "pending_approval",
                "booking": "send_calcom_link_only",
                "calcom_shadow_audit_url": CALCOM_SHADOW_AUDIT_URL,
            },
        }

    def get_onboarding(self) -> Dict[str, Any]:
        workspaces = list(self.onboarding_workspaces.values())
        workspaces.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return {
            "items": deepcopy(workspaces),
            "seed_drafts": deepcopy(list(self.onboarding_seed_drafts.values())),
            "intake_items": deepcopy(self.onboarding_intake_items[-50:]),
            "template_steps": [
                {"id": step_id, "label": label, "description": description}
                for step_id, label, description in ONBOARDING_STEPS
            ],
            "policy": {
                "trigger": "post_payment",
                "sensitive_steps": "pending_approval",
                "connections": [
                    "telegram",
                    "facebook",
                    "instagram",
                    "tiktok",
                    "linkedin",
                    "stripe",
                    "rut_dian",
                    "calcom",
                ],
            },
        }

    def get_service_desk(self, company_id: str = "", limit: int = 50) -> Dict[str, Any]:
        tickets = list(self.service_tickets.values())
        if company_id:
            tickets = [ticket for ticket in tickets if ticket.get("company_id") == company_id]
        tickets.sort(key=lambda item: item.get("updated_at") or "", reverse=True)
        return {"items": deepcopy(tickets[:limit]), "total": len(tickets)}

    def create_service_ticket(
        self,
        company_id: str,
        channel: str,
        actor_handle: str,
        subject: str,
        body: str,
        source_event_id: str = "",
    ) -> Dict[str, Any]:
        if not company_id.strip():
            raise ValueError("company_id is required")
        channel = _safe_channel(channel)
        subject_text = (subject or "").strip() or "Solicitud"
        body_text = (body or "").strip()
        if not body_text:
            raise ValueError("body is required")

        fingerprint = source_event_id.strip() or self._fingerprint(channel, actor_handle, subject_text + body_text)
        key = (company_id, fingerprint)
        if key in self.service_ticket_index:
            ticket = self.service_tickets[self.service_ticket_index[key]]
            ticket["duplicate_count"] = ticket.get("duplicate_count", 0) + 1
            ticket["updated_at"] = utc_now()
            return deepcopy(ticket)

        triage = self._triage_service_request(body_text)
        ticket_id = str(uuid4())
        ticket = {
            "id": ticket_id,
            "company_id": company_id,
            "channel": channel,
            "actor_handle": actor_handle or "client",
            "subject": subject_text,
            "body": body_text,
            "category": triage["category"],
            "priority": triage["priority"],
            "level": triage["level"],
            "status": "open",
            "assigned_to": triage["assigned_to"],
            "requires_human_review": triage["requires_human_review"],
            "duplicate_count": 0,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        self.service_tickets[ticket_id] = ticket
        self.service_ticket_index[key] = ticket_id
        self.service_ticket_comments.append(
            {
                "id": str(uuid4()),
                "ticket_id": ticket_id,
                "author": actor_handle or "client",
                "message": body_text,
                "created_at": utc_now(),
            }
        )
        self._record_agent_run(
            "ServiceDeskTriageAgent",
            lead_id=None,
            event_id=None,
            output={"ticket_id": ticket_id, "level": ticket["level"], "priority": ticket["priority"]},
        )
        self._mirror_supabase("service_desk_tickets", ticket)
        return deepcopy(ticket)

    def draft_service_reply(self, ticket_id: str, reply_text: str, actor_handle: str = "taty") -> Dict[str, Any]:
        ticket = self.service_tickets.get(ticket_id)
        if not ticket:
            raise KeyError("ticket_id not found")
        text = reply_text.strip()
        if not text:
            raise ValueError("reply_text is required")
        draft = {
            "id": str(uuid4()),
            "ticket_id": ticket_id,
            "status": "pending_approval",
            "requires_approval": True,
            "approval_reason": "Respuestas en canales externos quedan como borradores aprobables.",
            "actor_handle": actor_handle,
            "reply_text": text,
            "created_at": utc_now(),
        }
        self.service_reply_drafts[draft["id"]] = draft
        self._mirror_supabase("service_desk_reply_drafts", draft)
        return deepcopy(draft)

    def start_onboarding(
        self,
        company_name: str,
        customer_email: str,
        payment_reference: str,
        plan_name: str = "Starter",
        owner_handle: str = "",
        requested_channels: Optional[List[str]] = None,
        company_id: str = "",
    ) -> Dict[str, Any]:
        if not company_name.strip() or not customer_email.strip() or not payment_reference.strip():
            raise ValueError("company_name, customer_email and payment_reference are required")

        workspace = {
            "id": str(uuid4()),
            "company_id": company_id.strip() or None,
            "company_name": company_name.strip(),
            "customer_email": customer_email.strip(),
            "payment_reference": payment_reference.strip(),
            "plan_name": plan_name.strip() or "Starter",
            "owner_handle": owner_handle.strip() or customer_email.strip(),
            "status": "active",
            "current_step": "s1_kickoff",
            "requested_channels": requested_channels or ["telegram", "instagram", "linkedin"],
            "steps": self._build_onboarding_steps(),
            "training_profile": {
                "brand_voice": "pendiente",
                "tax_context": "pendiente",
                "offer_map": "pendiente",
                "content_pillars": [],
            },
            "sla": {
                "client_credentials_response_hours": 48,
                "contexia_response_hours_business": 4,
                "schedule_shift_policy": "Por cada dia de retraso del cliente, el cronograma se desplaza 1 dia.",
            },
            "qa_targets": {
                "api_connections": "100% activas, latencia <2s",
                "historical_reconciliation": ">=98% transacciones reconciliadas",
                "accounting_integrity": "debe=haber en muestra 50 docs",
                "centinela_tests": "detecta 3 escenarios inyectados",
                "adoption_day7": ">=3 logins al dashboard en 7 dias post Go-Live",
            },
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        # First step is operational kickoff; always needs explicit confirmation to move forward.
        workspace["steps"][0]["status"] = "pending_approval"
        self.onboarding_workspaces[workspace["id"]] = workspace
        self._record_agent_run(
            "OnboardingCoworkerAgent",
            lead_id=None,
            event_id=None,
            output={
                "workspace_id": workspace["id"],
                "company_name": workspace["company_name"],
                "status": workspace["status"],
            },
        )
        self._mirror_supabase("social_onboarding_workspaces", self._onboarding_row(workspace))
        return deepcopy(workspace)

    def intake_onboarding(
        self,
        workspace_id: str,
        text: str,
        source: str = "dashboard",
        actor_handle: str = "",
    ) -> Dict[str, Any]:
        workspace = self.onboarding_workspaces.get(workspace_id)
        if not workspace:
            raise KeyError("workspace_id not found")
        message = text.strip()
        if not message:
            raise ValueError("text is required")

        extracted = self._extract_onboarding_facts(message)
        required = self._required_credentials_checklist(extracted)
        intake = {
            "id": str(uuid4()),
            "workspace_id": workspace_id,
            "source": source,
            "actor_handle": actor_handle or workspace.get("owner_handle") or "client",
            "text": message,
            "extracted": extracted,
            "missing": required["missing"],
            "present": required["present"],
            "created_at": utc_now(),
        }
        self.onboarding_intake_items.append(intake)

        # Merge extracted facts into workspace profile, keeping prior values when already confirmed.
        profile = workspace.setdefault("client_profile", {})
        for key, value in extracted.items():
            if value in (None, "", [], {}):
                continue
            if key not in profile or profile.get(key) in (None, "", [], {}):
                profile[key] = value

        workspace["updated_at"] = utc_now()
        self._record_agent_run(
            "OnboardingIntakeAgent",
            lead_id=None,
            event_id=None,
            output={"workspace_id": workspace_id, "missing": intake["missing"], "present": intake["present"]},
        )
        self._mirror_supabase("social_onboarding_intake_items", intake)
        self._mirror_supabase("social_onboarding_workspaces", self._onboarding_row(workspace), upsert=True)
        return deepcopy(intake)

    def get_active_onboarding_for_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        if not company_id:
            return None
        for workspace in self.onboarding_workspaces.values():
            if workspace.get("company_id") == company_id and workspace.get("status") == "active":
                return workspace
        return None

    def advance_onboarding_step(
        self,
        workspace_id: str,
        step_id: str,
        status: str = "completed",
        notes: str = "",
    ) -> Dict[str, Any]:
        workspace = self.onboarding_workspaces.get(workspace_id)
        if not workspace:
            raise KeyError("workspace_id not found")
        valid_statuses = {"ready", "pending_approval", "in_progress", "completed", "blocked"}
        if status not in valid_statuses:
            raise ValueError(f"Invalid onboarding step status: {status}")

        step = next((item for item in workspace["steps"] if item["id"] == step_id), None)
        if not step:
            raise KeyError("step_id not found")

        step["status"] = status
        step["notes"] = notes
        step["updated_at"] = utc_now()
        workspace["current_step"] = step_id
        workspace["updated_at"] = utc_now()
        if status == "completed":
            self._unlock_next_onboarding_step(workspace, step_id)
        self._record_agent_run(
            "OnboardingCoworkerAgent",
            lead_id=None,
            event_id=None,
            output={"workspace_id": workspace_id, "step_id": step_id, "status": status},
        )
        self._mirror_supabase("social_onboarding_workspaces", self._onboarding_row(workspace), upsert=True)
        return deepcopy(workspace)

    def create_onboarding_seed(
        self,
        workspace_id: str,
        business_summary: str = "",
        initial_channels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        workspace = self.onboarding_workspaces.get(workspace_id)
        if not workspace:
            raise KeyError("workspace_id not found")

        channels = initial_channels or workspace.get("requested_channels") or []
        client_profile = workspace.get("client_profile") or {}
        seed = {
            "id": str(uuid4()),
            "workspace_id": workspace_id,
            "status": "pending_approval",
            "requires_approval": True,
            "approval_reason": (
                "El seed inicial puede crear datos operativos, campanas y reglas de agente; "
                "queda como borrador aprobable."
            ),
            "business_summary": business_summary.strip(),
            "datasets": {
                "company_profile": {
                    "company_name": workspace["company_name"],
                    "customer_email": workspace["customer_email"],
                    "plan_name": workspace["plan_name"],
                    "nit": client_profile.get("nit"),
                    "rut_status": client_profile.get("rut_status"),
                    "erp": client_profile.get("erp"),
                    "banks": client_profile.get("banks"),
                    "payment_processors": client_profile.get("payment_processors"),
                },
                "content_ops": {
                    "channels": channels,
                    "default_campaign": "Auditoria Sombra post-onboarding",
                    "content_pillars": ["claridad fiscal", "proteccion DIAN", "formalizacion", "crecimiento"],
                },
                "onboarding": {
                    "timeline_days": 21,
                    "week_1_goal": "Kick-off y credenciales completas",
                    "week_2_goal": "Setup tecnico y QA listo (handoff dia 14)",
                    "week_3_goal": "Auditoria Sombra + mapeo PUC + Go-Live",
                },
                "pipeline": {
                    "stages": [stage_id for stage_id, _label in PIPELINE_STAGES],
                    "initial_stage": "diagnosticado",
                },
                "training": {
                    "voice_sample_required": True,
                    "tax_documents_required": ["RUT", "camara_comercio", "ventas_90_dias"],
                    "human_review_boundary": "Entidad A revisa servicios regulados.",
                },
            },
            "created_at": utc_now(),
        }
        self.onboarding_seed_drafts[seed["id"]] = seed
        workspace["steps"] = [
            {**step, "status": "pending_approval" if step["id"] == "initial_seed" else step["status"]}
            for step in workspace["steps"]
        ]
        workspace["updated_at"] = utc_now()
        self._record_agent_run(
            "OnboardingSeedAgent",
            lead_id=None,
            event_id=None,
            output={"workspace_id": workspace_id, "seed_draft_id": seed["id"], "status": seed["status"]},
        )
        self._mirror_supabase("social_onboarding_seed_drafts", seed)
        return deepcopy(seed)

    def simulate_event(
        self,
        channel: str,
        text: str,
        actor_handle: str,
        actor_name: str = "",
        event_type: str = "message",
        source_event_id: str = "",
        account_id: str = "",
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        normalized = {
            "channel": channel,
            "account_id": account_id or channel,
            "source_event_id": source_event_id,
            "event_type": event_type,
            "actor_handle": actor_handle,
            "actor_name": actor_name or actor_handle,
            "text": text,
            "raw_payload": raw_payload or {},
        }
        return self.ingest_normalized_event(normalized)

    def ingest_normalized_event(self, normalized_event: Dict[str, Any]) -> Dict[str, Any]:
        channel = _safe_channel(str(normalized_event.get("channel") or ""))
        text = str(normalized_event.get("text") or "").strip()
        if not text:
            raise ValueError("Social Ops event text is required")

        actor_handle = str(normalized_event.get("actor_handle") or "unknown")
        source_event_id = str(normalized_event.get("source_event_id") or "").strip()
        if not source_event_id:
            source_event_id = self._fingerprint(channel, actor_handle, text)

        key = (channel, source_event_id)
        if key in self.event_index:
            event = self.events[self.event_index[key]]
            event["duplicate_count"] = event.get("duplicate_count", 0) + 1
            return {
                "created": False,
                "event": deepcopy(event),
                "lead": deepcopy(self.leads.get(event.get("lead_id"))),
                "diagnosis": self.analyze_text(event["text"]),
            }

        lead = self._resolve_lead(
            channel=channel,
            actor_handle=actor_handle,
            actor_name=str(normalized_event.get("actor_name") or actor_handle),
        )
        diagnosis = self.analyze_text(text)
        event_id = str(uuid4())
        event = {
            "id": event_id,
            "channel": channel,
            "account_id": str(normalized_event.get("account_id") or channel),
            "source_event_id": source_event_id,
            "event_type": str(normalized_event.get("event_type") or "message"),
            "actor_handle": actor_handle,
            "actor_name": str(normalized_event.get("actor_name") or actor_handle),
            "text": text,
            "normalized_text": normalize_text(text),
            "pain_tags": diagnosis["pain_tags"],
            "intent": diagnosis["intent"],
            "urgency": diagnosis["urgency"],
            "status": "processed",
            "lead_id": lead["id"],
            "duplicate_count": 0,
            "received_at": utc_now(),
            "raw_payload": normalized_event.get("raw_payload") or {},
        }
        self.events[event_id] = event
        self.event_index[key] = event_id

        updated_lead = self._apply_diagnosis_to_lead(lead, diagnosis, text, channel)
        self._record_agent_run(
            "InboundInterceptorAgent",
            lead_id=updated_lead["id"],
            event_id=event_id,
            output={"intent": diagnosis["intent"], "urgency": diagnosis["urgency"]},
        )
        self._record_agent_run(
            "QualificationAgent",
            lead_id=updated_lead["id"],
            event_id=event_id,
            output={"maturity_stage": diagnosis["maturity_stage"], "score": diagnosis["score"]},
        )
        self._mirror_supabase("social_inbound_events", self._event_row(event))
        self._mirror_supabase("social_leads", self._lead_row(updated_lead), upsert=True)

        return {
            "created": True,
            "event": deepcopy(event),
            "lead": deepcopy(updated_lead),
            "diagnosis": diagnosis,
        }

    def diagnose(
        self,
        event_id: Optional[str] = None,
        lead_id: Optional[str] = None,
        notes: str = "",
    ) -> Dict[str, Any]:
        event = self.events.get(event_id or "") if event_id else None
        lead = self.leads.get(lead_id or "") if lead_id else None
        if event and not lead:
            lead = self.leads.get(event.get("lead_id"))
        if not event and not lead:
            raise KeyError("event_id or lead_id not found")

        source_text = " ".join(
            part
            for part in [
                event.get("text") if event else "",
                lead.get("last_message") if lead else "",
                notes,
            ]
            if part
        )
        diagnosis = self.analyze_text(source_text)
        if lead:
            lead = self._apply_diagnosis_to_lead(
                lead,
                diagnosis,
                source_text,
                event["channel"] if event else lead.get("primary_channel", "telegram"),
            )
            self._record_agent_run(
                "PipelineAgent",
                lead_id=lead["id"],
                event_id=event["id"] if event else None,
                output={"pipeline_stage": lead["pipeline_stage"]},
            )
            self._mirror_supabase("social_leads", self._lead_row(lead), upsert=True)

        handoff = self._handoff_payload(lead, diagnosis) if diagnosis["requires_handoff"] else None
        if handoff:
            self._record_agent_run(
                "HandoffAgent",
                lead_id=lead["id"] if lead else None,
                event_id=event["id"] if event else None,
                output=handoff,
            )
        return {"diagnosis": diagnosis, "lead": deepcopy(lead), "handoff": handoff}

    def parse_command(
        self,
        text: str,
        channel: str = "telegram",
        actor_handle: str = "",
        lead_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        channel = _safe_channel(channel)
        command_text = text.strip()
        if not command_text:
            raise ValueError("Command text is required")

        action = self._detect_command_action(command_text)
        draft = {
            "id": str(uuid4()),
            "channel": channel,
            "actor_handle": actor_handle or "operator",
            "lead_id": lead_id,
            "command_text": command_text,
            "action": action,
            "status": "pending_approval",
            "requires_approval": True,
            "risk_level": "sensitive" if action != "general_request" else "controlled",
            "approval_reason": (
                "Zero-UI commands create approvable drafts only; infrastructure, publishing "
                "and critical scheduling are never executed directly."
            ),
            "parsed_payload": self._build_command_payload(action, command_text),
            "created_at": utc_now(),
        }
        self.command_drafts[draft["id"]] = draft
        self._record_agent_run(
            "CommandAgent",
            lead_id=lead_id,
            event_id=None,
            output={"draft_id": draft["id"], "action": action, "status": draft["status"]},
        )
        self._mirror_supabase("social_command_drafts", self._command_row(draft))
        return deepcopy(draft)

    def draft_lead_reply(
        self,
        lead_id: str,
        channel: str,
        intent: str = "",
        include_shadow_audit_link: bool = True,
        actor_handle: str = "taty",
    ) -> Dict[str, Any]:
        lead = self.leads.get(lead_id)
        if not lead:
            raise KeyError("lead_id not found")
        channel = _safe_channel(channel)

        diagnosis = self.analyze_text(lead.get("last_message") or "")
        intent = intent or diagnosis.get("intent") or "inbound_question"

        message = self._build_lead_reply_message(lead, diagnosis, include_shadow_audit_link)
        draft = {
            "id": str(uuid4()),
            "type": "lead_reply",
            "lead_id": lead_id,
            "channel": channel,
            "intent": intent,
            "status": "pending_approval",
            "requires_approval": True,
            "approval_reason": "Respuestas outbound (DM/comentarios) se envian solo con aprobacion explicita.",
            "actor_handle": actor_handle,
            "message_text": message,
            "created_at": utc_now(),
        }
        self.reply_drafts[draft["id"]] = draft
        self._record_agent_run(
            "TatyLeadAgent",
            lead_id=lead_id,
            event_id=None,
            output={"draft_id": draft["id"], "status": draft["status"], "channel": channel},
        )
        self._mirror_supabase("social_reply_drafts", draft)
        return deepcopy(draft)

    def draft_sales_closure(
        self,
        lead_id: str,
        channel: str,
        objective: str = "shadow_audit_booking",
        actor_handle: str = "taty",
    ) -> Dict[str, Any]:
        lead = self.leads.get(lead_id)
        if not lead:
            raise KeyError("lead_id not found")
        channel = _safe_channel(channel)

        diagnosis = self.analyze_text(lead.get("last_message") or "")
        maturity = diagnosis.get("maturity_stage") or lead.get("maturity_stage") or "Informal"
        urgency = diagnosis.get("urgency") or lead.get("urgency") or "low"

        payload = {
            "objective": objective,
            "maturity_stage": maturity,
            "urgency": urgency,
            "calcom_shadow_audit_url": CALCOM_SHADOW_AUDIT_URL,
            "next_stage": diagnosis.get("next_stage"),
        }

        draft = {
            "id": str(uuid4()),
            "type": "sales_closure",
            "lead_id": lead_id,
            "channel": channel,
            "status": "pending_approval",
            "requires_approval": True,
            "approval_reason": "Cierre comercial y mensajes outbound se envian solo con aprobacion explicita.",
            "actor_handle": actor_handle,
            "sales_script": self._build_sales_script(maturity=maturity, urgency=urgency, pain_tags=diagnosis.get("pain_tags") or []),
            "message_text": self._build_sales_message_text(lead=lead, maturity=maturity, urgency=urgency),
            "payload": payload,
            "created_at": utc_now(),
        }
        self.sales_drafts[draft["id"]] = draft
        self._record_agent_run(
            "SalesCloserAgent",
            lead_id=lead_id,
            event_id=None,
            output={"draft_id": draft["id"], "objective": objective, "status": draft["status"]},
        )
        self._mirror_supabase("social_sales_drafts", draft)
        return deepcopy(draft)

    def get_approval_queue(self, limit: int = 200) -> Dict[str, Any]:
        items: List[Dict[str, Any]] = []

        def push(draft_type: str, draft: Dict[str, Any], summary: str) -> None:
            if draft.get("status") != "pending_approval":
                return
            items.append(
                {
                    "type": draft_type,
                    "id": draft.get("id"),
                    "status": draft.get("status"),
                    "created_at": draft.get("created_at"),
                    "requires_approval": bool(draft.get("requires_approval", True)),
                    "risk_level": draft.get("risk_level", draft.get("priority", "controlled")),
                    "summary": summary,
                    "payload": draft,
                }
            )

        for draft in self.command_drafts.values():
            push("command", draft, f"{draft.get('action')}: {str(draft.get('command_text') or '')[:120]}")
        for draft in self.onboarding_seed_drafts.values():
            push("onboarding_seed", draft, f"seed: {draft.get('workspace_id')}")
        for draft in self.reply_drafts.values():
            push("lead_reply", draft, f"reply: lead {draft.get('lead_id')} ({draft.get('channel')})")
        for draft in self.sales_drafts.values():
            push("sales_closure", draft, f"sales: lead {draft.get('lead_id')} ({draft.get('channel')})")
        for draft in self.service_reply_drafts.values():
            push("service_reply", draft, f"ticket {draft.get('ticket_id')}")

        items.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return {"items": deepcopy(items[:limit]), "total": len(items)}

    def approve_draft(self, draft_type: str, draft_id: str, approved_by: str) -> Dict[str, Any]:
        if not approved_by.strip():
            raise ValueError("approved_by is required")
        target = self._resolve_draft(draft_type, draft_id)
        if target.get("status") != "pending_approval":
            return deepcopy(target)
        target["status"] = "approved"
        target["approved_at"] = utc_now()
        target["approved_by"] = approved_by.strip()
        self._record_agent_run(
            "ApprovalAgent",
            lead_id=target.get("lead_id"),
            event_id=None,
            output={"type": draft_type, "draft_id": draft_id, "status": "approved"},
        )
        self._mirror_draft_row(draft_type, target, upsert=True)
        return deepcopy(target)

    def reject_draft(self, draft_type: str, draft_id: str, rejected_by: str, reason: str = "") -> Dict[str, Any]:
        if not rejected_by.strip():
            raise ValueError("rejected_by is required")
        target = self._resolve_draft(draft_type, draft_id)
        if target.get("status") != "pending_approval":
            return deepcopy(target)
        target["status"] = "rejected"
        target["rejected_at"] = utc_now()
        target["rejected_by"] = rejected_by.strip()
        target["rejection_reason"] = (reason or "").strip()
        self._record_agent_run(
            "ApprovalAgent",
            lead_id=target.get("lead_id"),
            event_id=None,
            output={"type": draft_type, "draft_id": draft_id, "status": "rejected"},
        )
        self._mirror_draft_row(draft_type, target, upsert=True)
        return deepcopy(target)

    def _resolve_draft(self, draft_type: str, draft_id: str) -> Dict[str, Any]:
        stores = {
            "command": self.command_drafts,
            "onboarding_seed": self.onboarding_seed_drafts,
            "lead_reply": self.reply_drafts,
            "sales_closure": self.sales_drafts,
            "service_reply": self.service_reply_drafts,
        }
        store = stores.get(draft_type)
        if not store:
            raise KeyError("unknown draft_type")
        draft = store.get(draft_id)
        if not draft:
            raise KeyError("draft_id not found")
        return draft

    def _mirror_draft_row(self, draft_type: str, draft: Dict[str, Any], upsert: bool) -> None:
        table = {
            "command": "social_command_drafts",
            "onboarding_seed": "social_onboarding_seed_drafts",
            "lead_reply": "social_reply_drafts",
            "sales_closure": "social_sales_drafts",
            "service_reply": "service_desk_reply_drafts",
        }.get(draft_type)
        if not table:
            return
        self._mirror_supabase(table, draft, upsert=upsert)

    def handle_telegram_update(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        events = normalize_telegram_update(update_data)
        results = []
        drafts = []
        for event in events:
            text = event["text"]
            if self.is_social_ops_command(text):
                drafts.append(
                    self.parse_command(
                        text=text,
                        channel="telegram",
                        actor_handle=event.get("actor_handle") or "",
                    )
                )
            results.append(self.ingest_normalized_event(event))
        return {"events": results, "command_drafts": drafts}

    @staticmethod
    def is_social_ops_command(text: str) -> bool:
        lower = normalize_text(text)
        prefixes = (
            "/ops",
            "/social",
            "/config",
            "/lead",
            "/pipeline",
            "/campana",
            "/campaña",
            "/auditoria",
            "/auditoría",
        )
        keywords = (
            "auditoria sombra",
            "auditoría sombra",
            "centro de costos",
            "conectar stripe",
            "integrar stripe",
            "publicar en",
            "campana",
            "campaña",
        )
        return lower.startswith(prefixes) or any(keyword in lower for keyword in keywords)

    def analyze_text(self, text: str) -> Dict[str, Any]:
        lower = normalize_text(text)
        pain_tags = [
            tag
            for tag, keywords in PAIN_KEYWORDS.items()
            if any(keyword in lower for keyword in keywords)
        ]

        if any(tag in pain_tags for tag in ["embargo", "proveedor_riesgo"]):
            urgency = "critical"
        elif any(tag in pain_tags for tag in ["multa_dian", "auditoria"]):
            urgency = "high"
        elif pain_tags:
            urgency = "medium"
        else:
            urgency = "low"

        maturity_stage = self._classify_maturity(lower, pain_tags)
        intent = self._detect_intent(lower, pain_tags)
        score = min(100, 35 + len(pain_tags) * 12 + (25 if urgency == "critical" else 0))
        next_stage = self._next_stage(intent, urgency, pain_tags)
        requires_handoff = urgency == "critical" or "proveedor_riesgo" in pain_tags

        return {
            "intent": intent,
            "pain_tags": pain_tags,
            "urgency": urgency,
            "maturity_stage": maturity_stage,
            "score": score,
            "next_stage": next_stage,
            "requires_handoff": requires_handoff,
            "safe_reply": self._safe_reply(intent, urgency, maturity_stage),
            "calcom_shadow_audit_url": CALCOM_SHADOW_AUDIT_URL,
        }

    def _resolve_lead(self, channel: str, actor_handle: str, actor_name: str) -> Dict[str, Any]:
        key = (channel, actor_handle)
        lead_id = self.lead_index.get(key)
        if lead_id:
            return self.leads[lead_id]

        lead = {
            "id": str(uuid4()),
            "primary_channel": channel,
            "actor_handle": actor_handle,
            "display_name": actor_name,
            "maturity_stage": "Informal",
            "pipeline_stage": "nuevo",
            "urgency": "low",
            "pain_tags": [],
            "score": 0,
            "last_message": "",
            "last_event_at": utc_now(),
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        self.leads[lead["id"]] = lead
        self.lead_index[key] = lead["id"]
        self._record_pipeline_event(lead, "nuevo", "Lead creado desde canal inbound")
        return lead

    def _apply_diagnosis_to_lead(
        self,
        lead: Dict[str, Any],
        diagnosis: Dict[str, Any],
        text: str,
        channel: str,
    ) -> Dict[str, Any]:
        previous_stage = lead.get("pipeline_stage")
        previous_maturity = lead.get("maturity_stage", "Informal")
        candidate_maturity = diagnosis["maturity_stage"]
        if MATURITY_ORDER[candidate_maturity] >= MATURITY_ORDER[previous_maturity]:
            lead["maturity_stage"] = candidate_maturity

        lead["primary_channel"] = lead.get("primary_channel") or channel
        lead["urgency"] = self._max_urgency(lead.get("urgency", "low"), diagnosis["urgency"])
        lead["pain_tags"] = sorted(set(lead.get("pain_tags", [])) | set(diagnosis["pain_tags"]))
        lead["score"] = max(int(lead.get("score") or 0), int(diagnosis["score"]))
        lead["last_message"] = text[-500:]
        lead["last_event_at"] = utc_now()
        lead["updated_at"] = utc_now()

        target_stage = diagnosis["next_stage"]
        if previous_stage != target_stage:
            lead["pipeline_stage"] = target_stage
            self._record_pipeline_event(
                lead,
                target_stage,
                f"Movido por PipelineAgent desde {previous_stage}",
            )
        return lead

    def _record_pipeline_event(self, lead: Dict[str, Any], stage: str, reason: str) -> None:
        event = {
            "id": str(uuid4()),
            "lead_id": lead["id"],
            "stage": stage,
            "reason": reason,
            "created_at": utc_now(),
        }
        self.pipeline_events.append(event)
        self._mirror_supabase("social_pipeline_events", event)

    def _record_agent_run(
        self,
        agent_name: str,
        lead_id: Optional[str],
        event_id: Optional[str],
        output: Dict[str, Any],
    ) -> None:
        run = {
            "id": str(uuid4()),
            "agent_name": agent_name,
            "lead_id": lead_id,
            "event_id": event_id,
            "status": "completed",
            "output": output,
            "created_at": utc_now(),
        }
        self.agent_runs.append(run)
        self._mirror_supabase("social_agent_runs", run)

    def _build_onboarding_steps(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": step_id,
                "label": label,
                "description": description,
                "status": "pending_approval" if index == 0 else "blocked",
                "approval_required": True,
                "notes": "",
                "updated_at": utc_now(),
            }
            for index, (step_id, label, description) in enumerate(ONBOARDING_STEPS)
        ]

    def _unlock_next_onboarding_step(self, workspace: Dict[str, Any], step_id: str) -> None:
        step_ids = [step["id"] for step in workspace["steps"]]
        try:
            index = step_ids.index(step_id)
        except ValueError:
            return
        if index + 1 >= len(workspace["steps"]):
            workspace["status"] = "completed"
            return
        next_step = workspace["steps"][index + 1]
        if next_step["status"] == "blocked":
            next_step["status"] = "pending_approval" if next_step["approval_required"] else "ready"
            next_step["updated_at"] = utc_now()

    def _classify_maturity(self, lower: str, pain_tags: List[str]) -> str:
        if "stripe" in pain_tags or "costos" in pain_tags or "nomina" in pain_tags:
            return "Formal Escalable"
        if any(word in lower for word in ["factura", "iva", "retencion", "retención", "nomina", "nómina"]):
            return "Formal Operativa"
        if "rut" in pain_tags or any(word in lower for word in ["registro mercantil", "camara", "cámara"]):
            return "Semi-formal"
        return "Informal"

    def _detect_intent(self, lower: str, pain_tags: List[str]) -> str:
        if any(tag in pain_tags for tag in ["embargo", "multa_dian", "proveedor_riesgo"]):
            return "risk_diagnosis"
        if "auditoria" in pain_tags:
            return "shadow_audit"
        if "stripe" in pain_tags:
            return "integration_setup"
        if "costos" in pain_tags:
            return "cost_control"
        if "rut" in pain_tags:
            return "formalization"
        return "inbound_question"

    def _next_stage(self, intent: str, urgency: str, pain_tags: List[str]) -> str:
        if urgency == "critical" or "proveedor_riesgo" in pain_tags:
            return "escalado_entidad_a"
        if intent == "shadow_audit" or urgency == "high":
            return "auditoria_sombra"
        if intent in {"formalization", "integration_setup"}:
            return "formalizacion"
        if intent == "cost_control":
            return "activacion_fase2"
        return "diagnosticado"

    def _safe_reply(self, intent: str, urgency: str, maturity_stage: str) -> str:
        if urgency == "critical":
            return (
                "Detectamos una senal de riesgo alto. El agente preparara contexto y "
                "escalara a revision humana de Entidad A antes de cualquier accion."
            )
        if intent == "shadow_audit":
            return (
                "Puedo enviarte el enlace de Auditoria Sombra para revisar riesgos sin "
                "reservar horarios automaticamente."
            )
        return (
            f"Diagnostico inicial: etapa {maturity_stage}. Puedo preparar una respuesta "
            "asistida y sugerir el siguiente paso comercial."
        )

    def _build_lead_reply_message(
        self, lead: Dict[str, Any], diagnosis: Dict[str, Any], include_shadow_audit_link: bool
    ) -> str:
        name = lead.get("display_name") or lead.get("actor_handle") or "hola"
        urgency = diagnosis.get("urgency") or "low"
        maturity = diagnosis.get("maturity_stage") or "Informal"
        pain = diagnosis.get("pain_tags") or []

        opener = f"Hola {name}, soy Taty de Contexia."
        if urgency in {"high", "critical"}:
            opener += " Vi tu caso y parece sensible; prefiero guiarte con un diagnostico rapido."

        bullets = []
        if "multa_dian" in pain or "embargo" in pain:
            bullets.append("1) Confirmemos si hay requerimiento o sancion activa y fechas limite.")
        if "rut" in pain:
            bullets.append("2) Verificamos si necesitas RUT y que obligaciones aplican segun tu actividad.")
        if "stripe" in pain:
            bullets.append("3) Revisamos tus canales de cobro (Stripe) para evitar sorpresas fiscales.")
        if not bullets:
            bullets.append("1) Te hago 3 preguntas para ubicarte y darte el siguiente paso.")

        next_step = ""
        if include_shadow_audit_link and diagnosis.get("next_stage") in {"auditoria_sombra", "formalizacion"}:
            next_step = (
                "\n\nSi quieres, te dejo el enlace de Auditoria Sombra (gratuita) para revisar tu caso: "
                f"{CALCOM_SHADOW_AUDIT_URL}"
            )
        safety = "\n\nNota: no ejecuto cambios de infraestructura ni agenda critica sin tu confirmacion."
        return f"{opener}\n\nEtapa estimada: {maturity}.\n\n" + "\n".join(bullets) + next_step + safety

    def _build_sales_script(self, maturity: str, urgency: str, pain_tags: List[str]) -> Dict[str, Any]:
        # Script is structured so Sales/CS can approve and send quickly.
        opener = "Gracias por escribir. Te ayudo a aclarar el riesgo y el siguiente paso."
        if urgency in {"high", "critical"}:
            opener = "Esto se ve sensible. Hagamos un diagnostico rapido y te digo el siguiente paso seguro."

        qualify = [
            "Que vendes y por que canal principal?",
            "Tienes RUT y facturacion activa?",
            "Tienes algun requerimiento o fecha limite hoy/esta semana?",
        ]
        if maturity in {"Formal Operativa", "Formal Escalable"}:
            qualify.append("Tienes centros de costos o separacion por canal (Stripe/ERP)?")

        offer = {
            "name": "Auditoria Sombra",
            "promise": "Diagnostico rapido para ubicar riesgos y plan de formalizacion sin friccion.",
            "cta": "Agendemos una sesion de 45 min.",
            "link": CALCOM_SHADOW_AUDIT_URL,
            "policy": "Se envia link; no se reserva sin confirmacion del prospecto.",
        }
        objections = [
            {"objection": "No tengo tiempo", "response": "Son 45 min y sales con un plan claro de pasos priorizados."},
            {"objection": "Me da miedo la DIAN", "response": "Justo por eso empezamos con diagnostico y priorizamos riesgo."},
            {"objection": "Cuanto cuesta", "response": "La Auditoria Sombra es el paso inicial; el plan depende de tu etapa y riesgos."},
        ]
        if "embargo" in pain_tags:
            objections.append({"objection": "Me embargaron", "response": "Escalamos a revision humana de Entidad A antes de cualquier accion."})

        return {
            "opener": opener,
            "qualification_questions": qualify,
            "offer": offer,
            "objection_handling": objections,
            "handoff_rule": "Si riesgo critical o proveedor_riesgo: crear handoff Entidad A.",
        }

    def _build_sales_message_text(self, lead: Dict[str, Any], maturity: str, urgency: str) -> str:
        name = lead.get("display_name") or lead.get("actor_handle") or "hola"
        tone = "directo y claro"
        if maturity == "Informal":
            tone = "calmo y simple"
        if urgency in {"high", "critical"}:
            tone = "prioritario y seguro"

        return (
            f"Hola {name}, soy Taty de Contexia. Te escribo en tono {tone}.\n\n"
            "Puedo hacer un diagnostico rapido para ubicarte y evitar sorpresas (DIAN, multas, embargos).\n"
            f"Si te sirve, agenda la Auditoria Sombra aqui: {CALCOM_SHADOW_AUDIT_URL}\n\n"
            "Nota: no se ejecuta nada sensible sin tu confirmacion."
        )

    def _handoff_payload(
        self, lead: Optional[Dict[str, Any]], diagnosis: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "status": "human_review_required",
            "legal_boundary": "Entidad B prepara contexto; Entidad A ejecuta servicio regulado.",
            "lead_id": lead["id"] if lead else None,
            "urgency": diagnosis["urgency"],
            "message": (
                "Revisar riesgo critico antes de responder o ejecutar acciones. "
                "No se agenda reunion sin confirmacion del prospecto."
            ),
            "calcom_shadow_audit_url": CALCOM_SHADOW_AUDIT_URL,
        }

    def _extract_onboarding_facts(self, text: str) -> Dict[str, Any]:
        lower = normalize_text(text)

        nit_match = re.search(r"\b(\d{6,12})(?:-\d)?\b", text)
        nit = nit_match.group(1) if nit_match else None

        erp = None
        if "siigo" in lower:
            erp = "siigo"
        elif "alegra" in lower:
            erp = "alegra"

        processors = []
        for name in ["stripe", "nequi", "pse", "payu", "mercadopago", "paypal"]:
            if name in lower:
                processors.append(name)

        banks = []
        for bank in [
            "bancolombia",
            "davivienda",
            "bbva",
            "banco de bogota",
            "banco popular",
            "itau",
            "banco caja social",
            "nu",
            "lulo",
        ]:
            if bank in lower:
                banks.append(bank)

        rut_status = None
        if "no tengo rut" in lower or "sin rut" in lower:
            rut_status = "missing"
        elif "tengo rut" in lower or "rut listo" in lower:
            rut_status = "present"

        dian_token = None
        if "token dian" in lower or "dian token" in lower:
            dian_token = "mentioned"

        channels = []
        for channel in ["telegram", "facebook", "instagram", "tiktok", "linkedin"]:
            if channel in lower:
                channels.append(channel)

        pain = []
        for tag, keywords in PAIN_KEYWORDS.items():
            if any(keyword in lower for keyword in keywords):
                pain.append(tag)

        return {
            "nit": nit,
            "rut_status": rut_status,
            "erp": erp,
            "banks": banks,
            "payment_processors": processors,
            "dian_token": dian_token,
            "preferred_channels": channels,
            "pain_tags": pain,
        }

    def _triage_service_request(self, text: str) -> Dict[str, Any]:
        lower = normalize_text(text)
        category = "general"
        if any(word in lower for word in ["error", "cae", "no carga", "502", "500", "bug", "no funciona"]):
            category = "incident"
        elif any(word in lower for word in ["factura", "dian", "rut", "iva", "renta", "sancion", "multa"]):
            category = "tax"
        elif any(word in lower for word in ["pago", "facturacion", "cobro", "suscripcion", "setup fee"]):
            category = "billing"
        elif any(word in lower for word in ["conectar", "integrar", "api", "token", "credencial", "siigo", "alegra", "stripe"]):
            category = "integration"
        elif any(word in lower for word in ["lead", "venta", "prospecto", "campana", "campaña", "inbound"]):
            category = "sales"

        priority = "normal"
        if any(word in lower for word in ["urgente", "hoy", "embargo", "requerimiento", "lista clinton"]):
            priority = "urgent"

        # L1/L2/L3 routing (simple MVP heuristics)
        if category in {"incident", "integration"}:
            level = "L2"
            assigned_to = "Delivery (Entidad B)"
        elif category in {"tax"}:
            level = "L3"
            assigned_to = "Entidad A (Tax/Legal)"
        elif category in {"sales"}:
            level = "L1"
            assigned_to = "Sales/CS (Entidad B)"
        else:
            level = "L1"
            assigned_to = "Customer Success (Entidad B)"

        requires_human_review = level in {"L2", "L3"} or priority == "urgent"
        return {
            "category": category,
            "priority": priority,
            "level": level,
            "assigned_to": assigned_to,
            "requires_human_review": requires_human_review,
        }
    def _required_credentials_checklist(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        present = []
        missing = []

        def mark(key: str, ok: bool) -> None:
            (present if ok else missing).append(key)

        mark("token_dian", extracted.get("dian_token") is not None)
        mark("erp_access", extracted.get("erp") is not None)
        mark("bank_access_readonly", bool(extracted.get("banks")))
        mark("payment_processor_keys", bool(extracted.get("payment_processors")))
        mark("rut", extracted.get("rut_status") == "present")
        return {"present": present, "missing": missing}

    def _detect_command_action(self, text: str) -> str:
        lower = normalize_text(text)
        if any(word in lower for word in ["stripe", "integrar", "conectar"]):
            return "connect_integration"
        if "centro de costos" in lower or "centro de costo" in lower:
            return "create_cost_center"
        if "auditoria sombra" in lower or "auditoría sombra" in lower or "agenda" in lower:
            return "schedule_shadow_audit"
        if "publicar" in lower or "postear" in lower:
            return "publish_content"
        if "campana" in lower or "campaña" in lower:
            return "update_campaign"
        return "general_request"

    def _build_command_payload(self, action: str, text: str) -> Dict[str, Any]:
        payload = {"source_text": text}
        if action == "schedule_shadow_audit":
            payload["calcom_shadow_audit_url"] = CALCOM_SHADOW_AUDIT_URL
            payload["booking_policy"] = "send_link_only"
        if action == "connect_integration":
            payload["target"] = "stripe" if "stripe" in normalize_text(text) else "unknown"
        return payload

    def _max_urgency(self, current: str, candidate: str) -> str:
        order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return candidate if order[candidate] >= order.get(current, 1) else current

    def _fingerprint(self, channel: str, actor_handle: str, text: str) -> str:
        digest = hashlib.sha256(f"{channel}:{actor_handle}:{normalize_text(text)}".encode()).hexdigest()
        return digest[:24]

    def _seed_demo(self) -> None:
        self.simulate_event(
            channel="instagram",
            event_type="comment",
            actor_handle="@dropship_amva",
            actor_name="Dropship AMVA",
            text="Me llego un requerimiento de la DIAN por ventas en TikTok y temo una multa.",
            source_event_id="demo-instagram-1",
        )
        self.simulate_event(
            channel="facebook",
            event_type="message",
            actor_handle="creadora.medellin",
            actor_name="Creadora Medellin",
            text="No tengo claro si necesito RUT para vender mis cursos digitales.",
            source_event_id="demo-facebook-1",
        )
        self.simulate_event(
            channel="linkedin",
            event_type="comment",
            actor_handle="ops-founder",
            actor_name="Founder Ops",
            text="Estamos conectando Stripe y necesitamos centro de costos por canal.",
            source_event_id="demo-linkedin-1",
        )
        self.parse_command(
            text="/ops conectar Stripe para la cuenta principal y crear centro de costos TikTok",
            channel="telegram",
            actor_handle="ctx_operator",
        )

        self.ideas[1] = {
            "id": 1,
            "tema_raw": "Que es Contexia y por que no somos contadores tradicionales",
            "pilar": "CLARIDAD",
            "formato_sugerido": "CARRUSEL",
            "status": "NUEVA",
            "score_potencial": 8,
        }
        self.ideas[2] = {
            "id": 2,
            "tema_raw": "5 beneficios de integrar IA con Notion para tu agencia",
            "pilar": "ACCION",
            "formato_sugerido": "VIDEO_CORTO",
            "status": "SELECCIONADA",
            "score_potencial": 7,
        }

    def list_ideas(self) -> Dict[str, Any]:
        """Return ideas for Operaciones/Ideas (prefers Supabase when configured)."""
        try:
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
                client = get_supabase()
                result = (
                    client.table("ideas")
                    .select("id, tema_raw, pilar, formato_sugerido, status, score_potencial")
                    .order("score_potencial", desc=True)
                    .execute()
                )
                if result.data:
                    return {"source": "supabase", "items": result.data}
        except Exception as exc:
            logger.warning("Ideas: supabase unavailable, using demo memory: %s", exc)
        items = list(self.ideas.values())
        items.sort(key=lambda item: int(item.get("score_potencial") or 0), reverse=True)
        return {"source": "demo_fallback", "items": deepcopy(items)}

    def update_idea_status(self, idea_id: int, status: str) -> Dict[str, Any]:
        status = str(status).strip().upper()
        if status not in {"NUEVA", "SELECCIONADA", "USADA", "DESCARTADA"}:
            raise ValueError("Invalid idea status")
        try:
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
                client = get_supabase()
                client.table("ideas").update({"status": status}).eq("id", idea_id).execute()
                return {"ok": True, "source": "supabase"}
        except Exception as exc:
            logger.warning("Ideas: update failed in supabase, falling back: %s", exc)
        idea = self.ideas.get(int(idea_id))
        if not idea:
            raise KeyError("idea_id not found")
        idea["status"] = status
        return {"ok": True, "source": "demo_fallback"}

    def generate_idea_draft(self, idea_id: int) -> Dict[str, Any]:
        idea_id_int = int(idea_id)
        items = self.list_ideas().get("items") or []
        idea = next((item for item in items if int(item.get("id") or -1) == idea_id_int), None)
        if not idea:
            raise KeyError("idea_id not found")

        # Use the existing social content agent prompt via llm_engine, but keep a
        # deterministic fallback so the endpoint stays usable when all providers fail.
        from agents.llm_engine import AllProvidersFailedError, get_ai_response

        prompt = f"Idea: {idea.get('tema_raw')}\nFormato: {idea.get('formato_sugerido')}\nPilar: {idea.get('pilar')}"
        system_prompt = (
            "Eres el equipo de marketing de Contexia. Genera un borrador listo para publicar "
            "en redes (LinkedIn/Instagram/Facebook). Responde en espanol, claro, directo, con CTA."
        )
        try:
            draft_text = get_ai_response(
                prompt=prompt,
                system_prompt=system_prompt,
                response_format="text",
                max_tokens=650,
                temperature=0.8,
            )
        except AllProvidersFailedError as exc:
            logger.warning("IdeasDraftAgent: all providers failed, using deterministic fallback: %s", exc)
            tema = str(idea.get("tema_raw") or "").strip()
            formato = str(idea.get("formato_sugerido") or "POST").strip()
            pilar = str(idea.get("pilar") or "CLARIDAD").strip()
            draft_text = (
                f"Hook: {tema}.\n\n"
                f"Formato sugerido: {formato}.\n"
                f"Pilar editorial: {pilar}.\n\n"
                "Borrador base:\n"
                "En Contexia ayudamos a convertir contenido en decisiones claras y accionables. "
                "Si quieres un sistema orgánico que atraiga oportunidades de forma consistente, "
                "hablemos. Escribe 'Bunker' y te compartimos el siguiente paso."
            )

        self._record_agent_run(
            "IdeasDraftAgent",
            lead_id=None,
            event_id=None,
            output={"idea_id": idea_id_int, "status": "draft_generated"},
        )
        return {"idea_id": idea_id_int, "draft_text": draft_text}

    def get_metrics_dashboard(self) -> Dict[str, Any]:
        """Metrics dashboard for Operaciones/Métricas (prefers Supabase when configured)."""
        metricas = []
        publicaciones = []
        source = "demo_fallback"
        try:
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
                client = get_supabase()
                met = client.table("metricas").select("*").order("fecha_captura", desc=True).limit(200).execute()
                pubs = (
                    client.table("publicaciones")
                    .select("*")
                    .order("fecha_publicacion_real", desc=True)
                    .limit(200)
                    .execute()
                )
                metricas = met.data or []
                publicaciones = pubs.data or []
                source = "supabase"
        except Exception as exc:
            logger.warning("Metricas: supabase unavailable, using demo memory: %s", exc)

        if source == "demo_fallback":
            metricas = deepcopy(self.metrics)
            publicaciones = deepcopy(self.publications)

        total_alcance = sum(int(m.get("alcance") or 0) for m in metricas)
        total_posts = len(publicaciones) if publicaciones else len({m.get("pub_id") for m in metricas if m.get("pub_id")})
        avg_engagement = 0.0
        if metricas:
            avg_engagement = sum(float(m.get("engagement_rate") or 0) for m in metricas) / len(metricas)
        best_score = max([int(m.get("score") or 0) for m in metricas], default=0)

        return {
            "source": source,
            "summary": {
                "total_alcance": total_alcance,
                "avg_engagement_rate": round(avg_engagement, 2),
                "total_posts": total_posts,
                "best_score": best_score if best_score > 0 else None,
            },
            "metricas": metricas,
            "publicaciones": publicaciones,
        }

    def simulate_metrics(self) -> Dict[str, Any]:
        """Create demo metrics/publications for local smoke tests."""
        today = datetime.now(timezone.utc).date().isoformat()
        pub_id = len(self.publications) + 1
        self.publications.append(
            {
                "id": pub_id,
                "content_id": 1,
                "fecha_publicacion_real": today,
                "plataforma": "facebook",
                "url_post": None,
                "tipo_publicacion": "post",
                "notas_publicacion": "demo",
                "created_at": utc_now(),
            }
        )
        score = 78
        self.metrics.append(
            {
                "id": len(self.metrics) + 1,
                "pub_id": pub_id,
                "fecha_captura": today,
                "alcance": 12450,
                "impresiones": 16700,
                "reacciones": 480,
                "comentarios": 62,
                "compartidos": 31,
                "clics_link": 49,
                "guardados": 18,
                "engagement_rate": 6.12,
                "score": score,
                "clasificacion": "GANADOR",
                "insight_ia": "demo",
                "created_at": utc_now(),
            }
        )
        return self.get_metrics_dashboard()

    def _mirror_supabase(self, table: str, payload: Dict[str, Any], upsert: bool = False) -> None:
        if not self.persist_supabase:
            return
        if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
            return
        try:
            client = get_supabase()
            query = client.table(table)
            if upsert:
                query.upsert(payload).execute()
            else:
                query.insert(payload).execute()
        except Exception as exc:
            logger.warning("Social Ops Supabase mirror skipped for %s: %s", table, exc)

    def _event_row(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": event["id"],
            "channel": event["channel"],
            "account_id": event["account_id"],
            "source_event_id": event["source_event_id"],
            "event_type": event["event_type"],
            "actor_handle": event["actor_handle"],
            "actor_name": event["actor_name"],
            "text": event["text"],
            "normalized_text": event["normalized_text"],
            "pain_tags": event["pain_tags"],
            "urgency": event["urgency"],
            "status": event["status"],
            "lead_id": event["lead_id"],
            "raw_payload": event["raw_payload"],
            "received_at": event["received_at"],
        }

    def _lead_row(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": lead["id"],
            "primary_channel": lead["primary_channel"],
            "actor_handle": lead["actor_handle"],
            "display_name": lead["display_name"],
            "maturity_stage": lead["maturity_stage"],
            "pipeline_stage": lead["pipeline_stage"],
            "urgency": lead["urgency"],
            "pain_tags": lead["pain_tags"],
            "score": lead["score"],
            "last_message": lead["last_message"],
            "last_event_at": lead["last_event_at"],
            "created_at": lead["created_at"],
            "updated_at": lead["updated_at"],
        }

    def _command_row(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": draft["id"],
            "channel": draft["channel"],
            "actor_handle": draft["actor_handle"],
            "lead_id": draft["lead_id"],
            "command_text": draft["command_text"],
            "action": draft["action"],
            "status": draft["status"],
            "requires_approval": draft["requires_approval"],
            "risk_level": draft["risk_level"],
            "approval_reason": draft["approval_reason"],
            "parsed_payload": draft["parsed_payload"],
            "created_at": draft["created_at"],
        }

    def _onboarding_row(self, workspace: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": workspace["id"],
            "company_id": workspace.get("company_id"),
            "company_name": workspace["company_name"],
            "customer_email": workspace["customer_email"],
            "payment_reference": workspace["payment_reference"],
            "plan_name": workspace["plan_name"],
            "owner_handle": workspace["owner_handle"],
            "status": workspace["status"],
            "current_step": workspace["current_step"],
            "requested_channels": workspace["requested_channels"],
            "steps": workspace["steps"],
            "training_profile": workspace["training_profile"],
            "sla": workspace.get("sla", {}),
            "qa_targets": workspace.get("qa_targets", {}),
            "client_profile": workspace.get("client_profile", {}),
            "created_at": workspace["created_at"],
            "updated_at": workspace["updated_at"],
        }


_social_ops_service: Optional[SocialOpsService] = None


def get_social_ops_service() -> SocialOpsService:
    global _social_ops_service
    if _social_ops_service is None:
        _social_ops_service = SocialOpsService()
    return _social_ops_service
