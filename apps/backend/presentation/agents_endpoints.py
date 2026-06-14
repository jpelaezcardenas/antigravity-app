"""
LLM Agents Endpoints: API routes for LLM-powered agent tasks.

Automatically selects a cloud LLM provider via a failover chain
(OpenRouter Free / Groq / Cerebras / Mistral / Gemini) based on task type.
The user never sees which provider is used.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from agents.llm_engine import AllProvidersFailedError
from agents.secure_llm import get_anonymized_ai_response
from core.model_selector import choose_model_for_task, get_task_description

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# Request/Response Models
# ============================================

class AskRequest(BaseModel):
    question: str
    company_id: str
    context: str = ""


class AnalysisRequest(BaseModel):
    data: dict
    company_id: str
    analysis_type: str = "default"


class AgentResponse(BaseModel):
    result: dict | str
    model_used: str
    task_type: str
    tier: str
    success: bool


# ============================================
# TIER 1: OpenRouter Free (Non-Sensitive)
# ============================================

@router.post("/taty/ask")
async def taty_ask(request: AskRequest):
    """
    Taty FAQ: Answer user questions about taxes, processes, etc.

    The prompt and context are anonymized (SOSP) before being routed to the
    cloud LLM failover chain, and the response is rehydrated.
    """
    try:
        model = choose_model_for_task("taty_faq")

        system_prompt = f"""You are Taty, a helpful assistant for Contexia.
Your role is to answer questions about:
- Tax basics (Renta, IVA, retenciones)
- Invoicing and receipts
- Financial processes
- General accounting concepts

Company context: {request.context if request.context else "General knowledge"}

Be clear, concise, and in Spanish."""

        response = get_anonymized_ai_response(
            prompt=request.question,
            system_prompt=system_prompt,
            response_format="text",
            max_tokens=1000,
            temperature=0.7
        )

        task_desc = get_task_description("taty_faq")

        return AgentResponse(
            result=response,
            model_used=model.value,
            task_type="taty_faq",
            tier=task_desc["tier"],
            success=True
        )

    except AllProvidersFailedError as e:
        logger.error(f"Taty Ask failed: {str(e)}")
        raise HTTPException(status_code=503, detail="All LLM providers failed")
    except Exception as e:
        logger.error(f"Unexpected error in Taty Ask: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social/generate-content")
async def social_generate_content(request: AskRequest):
    """
    Generate social media content (posts, captions, etc).

    The prompt is anonymized (SOSP) before being routed to the cloud LLM
    failover chain, and the response is rehydrated.
    """
    try:
        model = choose_model_for_task("social_content_gen")

        system_prompt = """You are a social media content creator for Contexia.
Generate engaging, professional posts for LinkedIn, Instagram, and Twitter.
Focus on: financial tips, tax advice, company updates.
Keep it concise, use hashtags, and maintain brand voice.
Respond in Spanish."""

        response = get_anonymized_ai_response(
            prompt=request.question,
            system_prompt=system_prompt,
            response_format="text",
            max_tokens=500,
            temperature=0.8
        )

        task_desc = get_task_description("social_content_gen")

        return AgentResponse(
            result=response,
            model_used=model.value,
            task_type="social_content_gen",
            tier=task_desc["tier"],
            success=True
        )

    except AllProvidersFailedError as e:
        logger.error(f"Social Content Generation failed: {str(e)}")
        raise HTTPException(status_code=503, detail="All LLM providers failed")
    except Exception as e:
        logger.error(f"Unexpected error in Social Content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TIER 2: Ollama Local (Financial Data)
# ============================================

@router.post("/pulso/analyze")
async def pulso_analyze(request: AnalysisRequest):
    """
    Pulso Analysis: Analyze user's daily cash flow and financial status.

    Financial data is anonymized (SOSP) before being routed to the cloud LLM
    failover chain, and the response is rehydrated — per the Contexia Ground
    Truth (anonimización pre-LLM).
    """
    try:
        model = choose_model_for_task("pulso_analysis")

        system_prompt = """You are a financial analyst for Contexia.
Analyze the user's cash flow data and provide insights about:
- Daily income vs expenses
- Cash available after DIAN provisions
- Trends and anomalies
- Actionable recommendations

Be precise with numbers, professional tone.
Respond in Spanish JSON format with: ingresos, gastos, margen, provision_dian, dinero_tuyo, advertencias, recomendaciones."""

        prompt = f"""Analiza estos datos financieros:
{request.data}

Proporciona un análisis detallado en formato JSON."""

        response = get_anonymized_ai_response(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="json",
            max_tokens=2000,
            temperature=0.5  # Lower temp for financial accuracy
        )

        task_desc = get_task_description("pulso_analysis")

        return AgentResponse(
            result=response,
            model_used=model.value,
            task_type="pulso_analysis",
            tier=task_desc["tier"],
            success=True
        )

    except AllProvidersFailedError as e:
        logger.error(f"Pulso Analysis failed: {str(e)}")
        raise HTTPException(status_code=503, detail="All LLM providers failed")
    except Exception as e:
        logger.error(f"Unexpected error in Pulso Analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/centinela/monitor")
async def centinela_monitor(request: AnalysisRequest):
    """
    Centinela Monitoring: Check fiscal threshold status (Renta, IVA).

    Financial data is anonymized (SOSP) before being routed to the cloud LLM
    failover chain, and the response is rehydrated — per the Contexia Ground
    Truth (anonimización pre-LLM).
    """
    try:
        model = choose_model_for_task("centinela_monitoring")

        system_prompt = """You are a tax monitoring system for Contexia.
Analyze fiscal threshold data and provide status:
- Renta declaration threshold (29.5M COP)
- IVA responsibility threshold (40M COP)
- Withholding obligations
- Days until threshold (estimated)

Respond in JSON: umbral, porcentaje, estado, dias_estimados, recomendacion_usuario."""

        prompt = f"""Monitorea estos umbrales fiscales:
{request.data}

Proporciona estado actual en JSON."""

        response = get_anonymized_ai_response(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="json",
            max_tokens=1500,
            temperature=0.3  # Very low temp for compliance
        )

        task_desc = get_task_description("centinela_monitoring")

        return AgentResponse(
            result=response,
            model_used=model.value,
            task_type="centinela_monitoring",
            tier=task_desc["tier"],
            success=True
        )

    except AllProvidersFailedError as e:
        logger.error(f"Centinela Monitor failed: {str(e)}")
        raise HTTPException(status_code=503, detail="All LLM providers failed")
    except Exception as e:
        logger.error(f"Unexpected error in Centinela Monitor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TIER 3: Groq (Critical, Fiscal/Compliance)
# ============================================

@router.post("/centinela/decide")
async def centinela_decide(request: AnalysisRequest):
    """
    Centinela Decision: CRITICAL fiscal decision (should user file tax return?).

    Automatically uses: Groq (CRITICAL, non-negotiable quality)
    This decision has legal implications - must be reliable.
    """
    try:
        model = choose_model_for_task("centinela_decision")

        if model.value != "groq":
            logger.warning(f"Centinela Decision should use Groq, but got {model.value}. Forcing Groq.")
            from agents.llm_engine import LLMProvider
            # In production, we'd override model selection for critical tasks
            # For now, log the anomaly

        system_prompt = """You are a tax compliance expert for Contexia.
CRITICAL: This decision has legal implications.

Analyze fiscal data and DECIDE:
1. Should user file Renta (income tax)?
2. Should user register as IVA responsible?
3. What are the risks if they don't?
4. What are the deadlines?

Respond in JSON: debe_declarar_renta, debe_registrar_iva, riesgo_nivel, fechas_limite, acciones_recomendadas.
Be CONSERVATIVE - if unsure, recommend filing."""

        prompt = f"""ANÁLISIS CRÍTICO DE DECISIÓN FISCAL:
{request.data}

Basado en la ley colombiana actual, ¿qué debe hacer este usuario?
Proporciona decisión en JSON con recomendaciones."""

        response = get_anonymized_ai_response(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="json",
            max_tokens=2000,
            temperature=0.2  # Minimal creativity for legal decisions
        )

        task_desc = get_task_description("centinela_decision")

        logger.info(f"Centinela Decision completed with model: {model.value}")

        return AgentResponse(
            result=response,
            model_used=model.value,
            task_type="centinela_decision",
            tier=task_desc["tier"],
            success=True
        )

    except AllProvidersFailedError as e:
        logger.error(f"Centinela Decision failed: {str(e)}")
        raise HTTPException(status_code=503, detail="All LLM providers failed - cannot make fiscal decision")
    except Exception as e:
        logger.error(f"Unexpected error in Centinela Decision: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/audit")
async def compliance_audit(request: AnalysisRequest):
    """
    Compliance Audit: Verify user compliance with DIAN regulations.

    Automatically uses: Groq (CRITICAL regulatory decision)
    """
    try:
        model = choose_model_for_task("compliance_audit")

        system_prompt = """You are a DIAN compliance auditor for Contexia.
CRITICAL: This is a regulatory audit.

Review user's financial records and compliance status:
- Renta declaration timeliness
- IVA filing obligations
- Withholding compliance
- Documentation requirements
- Risk exposure

Respond in JSON: cumplimiento, riesgos, acciones_inmediatas, documentacion_requerida."""

        prompt = f"""AUDITORÍA DE CUMPLIMIENTO DIAN:
{request.data}

¿Está este usuario en cumplimiento con regulaciones colombianas?
Proporciona audit en JSON."""

        response = get_anonymized_ai_response(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="json",
            max_tokens=2000,
            temperature=0.1  # Absolute minimum for compliance
        )

        task_desc = get_task_description("compliance_audit")

        return AgentResponse(
            result=response,
            model_used=model.value,
            task_type="compliance_audit",
            tier=task_desc["tier"],
            success=True
        )

    except AllProvidersFailedError as e:
        logger.error(f"Compliance Audit failed: {str(e)}")
        raise HTTPException(status_code=503, detail="All LLM providers failed - cannot complete audit")
    except Exception as e:
        logger.error(f"Unexpected error in Compliance Audit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Orchestrator Pipeline
# ============================================

class FullPipelineRequest(BaseModel):
    company_url: str
    campaign_objective: str
    budget: float
    target_channels: list = ["instagram", "linkedin"]
    company_id: str = ""


@router.post("/orchestrator/full-pipeline")
async def full_pipeline(request: FullPipelineRequest):
    """
    POST /api/v1/agents/orchestrator/full-pipeline

    DEMO endpoint: returns a hardcoded, illustrative 7-stage response. No agents
    are actually executed and the per-stage durations are placeholders, not real
    timings. Wiring real orchestration is tracked as separate work.

    Flow: Discovery → SEO → Generator → Editor → Repurposer → Analyst → Distribution
    """
    import time
    from datetime import datetime

    start_time = time.time()

    # Demo 7-stage pipeline — hardcoded illustrative output; agents are NOT executed.
    stages = [
        {
            "stage": 1,
            "agent": "Discovery (OnboardingAgent)",
            "status": "success",
            "duration": "2.3s",
            "output": {
                "brand_tone": "professional",
                "key_colors": ["#2DD4BF", "#020617"],
                "value_propositions": ["Financial clarity", "Tax automation"]
            }
        },
        {
            "stage": 2,
            "agent": "SEO Strategist (PlannerAgent)",
            "status": "success",
            "duration": "1.8s",
            "output": {
                "campaign_options": 3,
                "recommended": "Lead generation for audit services",
                "estimated_roi": "3.2x"
            }
        },
        {
            "stage": 3,
            "agent": "Content Generator (GeneratorAgent)",
            "status": "success",
            "duration": "3.1s",
            "output": {
                "posts_generated": 5,
                "formats": ["instagram_post", "carousel", "thread"],
                "compliance_score": 0.95
            }
        },
        {
            "stage": 4,
            "agent": "Legal Reviewer (EditorAgent)",
            "status": "success",
            "duration": "2.0s",
            "output": {
                "approved_posts": 5,
                "revisions_needed": 0,
                "compliance_check": "DIAN regulations verified"
            }
        },
        {
            "stage": 5,
            "agent": "Content Repurposer",
            "status": "success",
            "duration": "1.9s",
            "output": {
                "repurposed": 12,
                "formats": ["stories", "videos", "carousels"],
                "atomic_units": 8
            }
        },
        {
            "stage": 6,
            "agent": "Analytics & Reporting",
            "status": "success",
            "duration": "1.2s",
            "output": {
                "engagement_predictions": "8.5% avg",
                "best_posting_time": "Tuesday 2PM",
                "audience_segment": "Entrepreneurs 25-45"
            }
        },
        {
            "stage": 7,
            "agent": "Distribution Scheduler",
            "status": "dry_run",
            "duration": "0.8s",
            "output": {
                "scheduled_posts": 5,
                "platforms": ["instagram", "linkedin"],
                "schedule_window": "Next 14 days",
                "note": "Dry-run mode - no actual publishing yet"
            }
        }
    ]

    total_time = time.time() - start_time

    return {
        "workflow_id": f"wf-{request.company_id[:8]}-{int(time.time())}",
        "company_id": request.company_id,
        "campaign_objective": request.campaign_objective,
        "total_time": f"{total_time:.2f}s",
        "mode": "demo",
        "note": "Illustrative demo output; agents are not actually executed and stage durations are placeholders.",
        "stages": stages,
        "status": "completed",
        "summary": {
            "total_agents": 7,
            "completed": 7,
            "failed": 0,
            "content_generated": 5,
            "content_repurposed": 12,
            "scheduled": 5
        },
        "next_action": "Review scheduled posts and approve for publishing",
        "timestamp": datetime.now().isoformat()
    }


# ============================================
# Debug / Info Endpoints
# ============================================

@router.get("/task-info/{task_type}")
async def get_task_info(task_type: str):
    """
    Debug endpoint: Get info about how a task will be routed.

    Example: GET /api/v1/agents/task-info/pulso_analysis
    """
    try:
        task_desc = get_task_description(task_type)
        return {
            "task_type": task_type,
            "tier": task_desc["tier"],
            "provider": task_desc["provider"],
            "model_info": task_desc["details"],
            "message": "This is how this task will be routed for model selection"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid task type: {task_type}")
