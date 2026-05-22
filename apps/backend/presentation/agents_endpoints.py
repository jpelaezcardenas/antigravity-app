"""
Agent Orchestrator API Endpoints - FASE 2
Exposes the 7-agent system for campaign generation via REST API
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Optional, List
from agents.agent_orchestrator import AgentOrchestrator, create_full_campaign
from datetime import datetime
import re

router = APIRouter()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def sanitize_error_message(error_msg: str) -> str:
    """
    Remove problematic characters from error messages for Windows charmap encoding
    Replace emoji and special Unicode with placeholder text
    """
    try:
        # Try to encode as ASCII; if it fails, remove problematic characters
        error_msg.encode('ascii')
        return error_msg
    except UnicodeEncodeError:
        # Remove emoji and special characters, keep only ASCII and basic accents
        return error_msg.encode('ascii', errors='replace').decode('ascii').replace('?', '')


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class FullCampaignRequest(BaseModel):
    """Request to generate a complete campaign end-to-end"""
    company_url: str
    campaign_objective: str
    budget: float = 5000


class AgentStatusResponse(BaseModel):
    """Response with agent status"""
    agent_name: str
    version: str
    stats: Dict


class CampaignGenerationResponse(BaseModel):
    """Response from full campaign generation"""
    workflow_id: str
    status: str
    campaign: Dict
    database_campaign_id: Optional[str] = None
    persisted: bool = False


class ReviewContentRequest(BaseModel):
    """Request to review content for compliance"""
    content: Dict
    tax_dna: Dict
    language: str = "es"
    strict_mode: bool = False


# ============================================================================
# CONTEXIA SERVICES REQUEST MODELS
# ============================================================================

class PulsoDiariosRequest(BaseModel):
    """Request for Pulso Diario daily KPI snapshot"""
    company_id: str


class CentinelaCheckRequest(BaseModel):
    """Request for Centinela risk assessment"""
    company_id: str


class TatyQuestionRequest(BaseModel):
    """Request to ask Taty a question"""
    company_id: str
    question: str
    language: str = "es"


class FullPipelinePersistenceRequest(BaseModel):
    """Request for full pipeline with database persistence"""
    company_url: str
    campaign_objective: str
    budget: float = 5000
    target_channels: Optional[List[str]] = None
    company_id: Optional[str] = None
    save_to_db: bool = True


class OnboardingAnalyzeRequest(BaseModel):
    """Request for Onboarding Agent analysis"""
    company_url: str
    company_data: Optional[Dict] = None


class PlannerGenerateRequest(BaseModel):
    """Request for Planner Agent campaign options"""
    campaign_objective: str
    tax_dna: Dict
    budget: float = 5000
    timeline_weeks: int = 4


class GeneratorCreateRequest(BaseModel):
    """Request for Generator Agent content creation"""
    campaign: Dict
    tax_dna: Dict
    channel: str = "instagram"
    variations_count: int = 3


class RepurposerTransformRequest(BaseModel):
    """Request for Repurposer Agent transformation"""
    source_content: str
    source_type: str = "article"
    target_formats: Optional[List[str]] = None


class AnalystAnalyzeRequest(BaseModel):
    """Request for Analyst Agent metrics analysis"""
    campaign_id: str
    metrics: Dict
    period_days: int = 7


class DistributionScheduleRequest(BaseModel):
    """Request for Distribution Agent publishing schedule"""
    posts: List[Dict]
    channels_config: Dict
    dry_run: bool = True


# ============================================================================
# AGENT ORCHESTRATOR ENDPOINTS
# ============================================================================

@router.post("/orchestrator/full-campaign", response_model=Dict, tags=["agents"])
async def generate_full_campaign(request: FullCampaignRequest):
    """
    Generate complete campaign end-to-end using Agent Orchestrator

    Workflow:
    1. Onboarding Agent → Extract Tax DNA from company_url
    2. Planner Agent → Generate campaign options
    3. Generator Agent → Create content variations
    4. Save to database

    Args:
        company_url: Company website URL to analyze
        campaign_objective: What the campaign should achieve
        budget: Total campaign budget

    Returns:
        Complete campaign ready to publish with:
        - Tax DNA profile
        - Campaign option (top-ranked)
        - Content variations (3+ per channel)
        - Database campaign ID (persisted)
    """
    try:
        result = create_full_campaign(
            company_url=request.company_url,
            objective=request.campaign_objective,
            budget=request.budget
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign generation failed: {str(e)}")


@router.get("/orchestrator/status", response_model=Dict, tags=["agents"])
async def get_orchestrator_status():
    """
    Get orchestrator statistics and agent statuses

    Returns:
        - Total executions
        - Success/failure rates
        - Active agents
        - Agent versions
    """
    try:
        orchestrator = AgentOrchestrator()
        return {
            "orchestrator": {
                "name": orchestrator.name,
                "version": orchestrator.version,
                "created_at": orchestrator.created_at
            },
            "agents": orchestrator.get_all_agents(),
            "execution_stats": orchestrator.get_execution_stats(),
            "campaigns_count": len(orchestrator.list_campaigns())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/orchestrator/executions", response_model=Dict, tags=["agents"])
async def get_execution_history(limit: int = Query(10, ge=1, le=100)):
    """
    Get recent workflow executions

    Args:
        limit: Number of recent executions to return (1-100)

    Returns:
        - List of recent executions with timestamps and statuses
        - Success/failure details
    """
    try:
        orchestrator = AgentOrchestrator()
        history = orchestrator.get_execution_history()
        return {
            "total_executions": len(history),
            "recent": history[-limit:] if history else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {sanitize_error_message(str(e))}")


@router.get("/orchestrator/campaigns", response_model=Dict, tags=["agents"])
async def list_campaigns():
    """
    Get all campaigns generated by orchestrator

    Returns:
        - Campaign IDs
        - Created timestamps
        - Current status (draft/active/completed)
    """
    try:
        orchestrator = AgentOrchestrator()
        campaigns = orchestrator.list_campaigns()
        return {
            "total_campaigns": len(campaigns),
            "campaigns": campaigns
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign list failed: {str(e)}")


# ============================================================================
# INDIVIDUAL AGENT ENDPOINTS
# ============================================================================

@router.post("/onboarding/analyze", response_model=Dict, tags=["agents"])
async def analyze_company(request: OnboardingAnalyzeRequest):
    """
    Use Onboarding Agent to extract Tax DNA from company

    Args:
        company_url: Company website URL
        company_data: Optional pre-scraped company data

    Returns:
        Tax DNA profile with:
        - Visual identity (colors, fonts, style)
        - Verbal identity (tone, key phrases, value propositions)
        - Services and pricing
        - Buyer personas (2+)
        - Compliance rules
        - Differentiation analysis
    """
    try:
        orchestrator = AgentOrchestrator()
        result = orchestrator._step_onboard(request.company_url)
        return {
            "status": "success",
            "tax_dna": result["tax_dna"],
            "validation": result["validation"],
            "personas": result["personas"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Onboarding analysis failed: {str(e)}")


@router.post("/planner/generate-options", response_model=Dict, tags=["agents"])
async def generate_campaign_options(request: PlannerGenerateRequest):
    """
    Use Planner Agent to generate campaign options

    Args:
        campaign_objective: Campaign goal
        tax_dna: Tax DNA profile from onboarding
        budget: Campaign budget
        timeline_weeks: Duration in weeks (default 4)

    Returns:
        - 3-5 campaign options
        - Top recommendation (ranked by ROI)
        - Budget analysis
    """
    try:
        orchestrator = AgentOrchestrator()
        result = orchestrator._step_plan(
            objective=request.campaign_objective,
            tax_dna=request.tax_dna,
            budget=request.budget
        )
        return {
            "status": "success",
            "campaign_options": result["campaign_options"],
            "recommendation": result["recommendation"],
            "budget_analysis": result["budget_analysis"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign planning failed: {str(e)}")


@router.post("/generator/create-content", response_model=Dict, tags=["agents"])
async def generate_content_variations(request: GeneratorCreateRequest):
    """
    Use Generator Agent to create content variations

    Args:
        campaign: Campaign option from planner
        tax_dna: Tax DNA profile
        channel: Target channel (instagram, linkedin, facebook, tiktok, email, whatsapp)
        variations_count: Number of variations to generate (default 3)

    Returns:
        - Multiple content variations per channel
        - Compliance checks performed
        - Ready-to-publish formats
    """
    try:
        orchestrator = AgentOrchestrator()
        result = orchestrator._step_generate(
            campaign_option=request.campaign,
            tax_dna=request.tax_dna
        )
        return {
            "status": "success",
            "channel": result["channel"],
            "variations": result["variations"],
            "total_variations": result["total_variations"],
            "generation_quality": result["generation_quality"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@router.post("/legal-reviewer/review-content", response_model=Dict, tags=["agents"])
async def review_content_compliance(request: ReviewContentRequest):
    """
    Use Legal Reviewer Agent to validate content for DIAN compliance

    Args:
        content: Generated content (posts, messages, etc.)
        tax_dna: Tax DNA profile with compliance rules
        language: Language for review (es/en, default: es)
        strict_mode: Enforce rules strictly (default: False)

    Returns:
        - Compliance status (pass/fail)
        - List of violations found
        - Approved content with disclaimers added
        - Risk level assessment (LOW/MEDIUM/HIGH)
        - Risk flags for human review
    """
    try:
        orchestrator = AgentOrchestrator()
        result = orchestrator._step_review(
            content=request.content,
            tax_dna=request.tax_dna,
            language=request.language
        )
        return {
            "status": "success",
            "compliance_check": {
                "is_compliant": result.get("is_compliant", False),
                "risk_level": result.get("risk_level", "UNKNOWN"),
                "violations_count": len(result.get("violations", [])),
                "violations": result.get("violations", []),
                "disclaimers_added": result.get("disclaimers_added", []),
                "risk_flags": result.get("risk_flags", []),
                "modified": result.get("modified", False),
                "summary": result.get("summary", "")
            },
            "approved_content": result.get("approved_content", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content review failed: {str(e)}")


@router.post("/repurposer/transform", response_model=Dict, tags=["agents"])
async def repurpose_content(request: RepurposerTransformRequest):
    """
    Use Repurposer Agent to transform content across formats

    Args:
        source_content: Original content piece
        source_type: Type of source (article, video, post)
        target_formats: List of target formats (twitter_thread, linkedin_post, tiktok_script, instagram_carousel, email, blog_post)

    Returns:
        - Multi-format repurposed variations
        - Atomic insights extracted
        - Reusability score
    """
    target_formats = request.target_formats or ["twitter_thread", "linkedin_post", "instagram_carousel"]

    try:
        orchestrator = AgentOrchestrator()
        # Get tax_dna from session/context (placeholder empty for now)
        result = orchestrator._step_repurpose(
            source_content=request.source_content,
            source_type=request.source_type,
            target_formats=target_formats,
            tax_dna={}
        )
        return {
            "status": "success",
            "repurposed": result.get("repurposed", []),
            "atomic_insights": result.get("atomic_insights", []),
            "total_variations": result.get("total_variations", 0),
            "reusability_score": result.get("reusability_score", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content repurposing failed: {str(e)}")


@router.post("/analyst/analyze-metrics", response_model=Dict, tags=["agents"])
async def analyze_campaign_metrics(request: AnalystAnalyzeRequest):
    """
    Use Analyst Agent to analyze campaign metrics and generate insights

    Args:
        campaign_id: Campaign identifier
        metrics: Dictionary with posts and engagement data
        period_days: Analysis period in days (default 7)

    Returns:
        - Performance analysis with top/bottom performers
        - Insights and patterns identified
        - Recommendations for optimization
        - KPI calculations
    """
    try:
        orchestrator = AgentOrchestrator()
        result = orchestrator._step_analyze(
            campaign_id=request.campaign_id,
            metrics=request.metrics,
            period_days=request.period_days
        )
        return {
            "status": "success",
            "campaign_id": result.get("campaign_id"),
            "total_posts_analyzed": result.get("total_posts_analyzed"),
            "statistics": result.get("statistics"),
            "top_performers": result.get("top_performers", []),
            "underperformers": result.get("underperformers", []),
            "insights": result.get("insights", {}),
            "recommendations": result.get("recommendations", []),
            "kpis": result.get("kpis", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics analysis failed: {str(e)}")


@router.post("/distribution/schedule-publishing", response_model=Dict, tags=["agents"])
async def schedule_content_publishing(request: DistributionScheduleRequest):
    """
    Use Distribution Agent to schedule content publishing (v0.1 dry-run mode)

    Args:
        posts: List of approved posts to publish
        channels_config: Configuration for each channel (API keys, account info)
        dry_run: If True, logs intent without calling real APIs (default True for v0.1)

    Returns:
        - Publishing schedule confirmation
        - Validation results
        - Dry-run publishing log
    """
    try:
        orchestrator = AgentOrchestrator()
        result = orchestrator._step_distribute(
            posts=request.posts,
            channels_config=request.channels_config,
            dry_run=request.dry_run
        )
        return {
            "status": "success",
            "total_posts": result.get("total_posts"),
            "scheduled": result.get("scheduled", []),
            "failed": result.get("failed", []),
            "dry_run": result.get("dry_run"),
            "next_steps": result.get("next_steps", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content distribution failed: {str(e)}")


# ============================================================================
# FULL PIPELINE ENDPOINT (7 AGENTS IN SEQUENCE)
# ============================================================================

class FullPipelineRequest(BaseModel):
    """Request for complete 7-agent pipeline execution"""
    company_url: str
    campaign_objective: str
    budget: float = 5000
    target_channels: Optional[list] = None
    execute_distribution: bool = False  # Set to True to trigger actual publishing


@router.post("/orchestrator/full-pipeline", response_model=Dict, tags=["agents"])
async def execute_full_pipeline(request: FullPipelineRequest):
    """
    Execute complete 7-agent pipeline from URL to publishing dry-run

    Workflow:
    1. Discovery Agent → Extract Tax DNA
    2. SEO Strategist Agent → Generate campaign options
    3. Generator Agent → Create content variations
    4. Editor Agent → Validate compliance
    5. Repurposer Agent → Multi-format transformation
    6. Analyst Agent → Performance analysis (if metrics available)
    7. Distribution Agent → Schedule publishing (dry-run by default)

    Args:
        company_url: Company website to analyze
        campaign_objective: Campaign goal
        budget: Campaign budget
        target_channels: Channels to target (instagram, linkedin, facebook, twitter)
        execute_distribution: If True, trigger real publishing (default False for safety)

    Returns:
        - Complete pipeline execution report
        - Results from all 7 agents
        - Timing per stage
        - Final campaign ready status
    """
    import time
    from datetime import datetime

    orchestrator = AgentOrchestrator()
    pipeline_start = time.time()

    try:
        # ====================================================================
        # STEP 1: DISCOVERY - Extract Tax DNA
        # ====================================================================
        step1_start = time.time()
        print(f"[STEP 1/7] Discovery Agent - Analyzing {request.company_url}...")

        onboarding_result = orchestrator._step_onboard(request.company_url)
        tax_dna = onboarding_result["tax_dna"]

        step1_time = time.time() - step1_start
        step1_output = {
            "agent": "Discovery",
            "status": "complete",
            "timing_seconds": round(step1_time, 2),
            "output": {
                "personas_extracted": len(tax_dna.get("buyer_personas", [])),
                "services": len(tax_dna.get("servicios", {}).get("primary_services", []))
            }
        }

        # ====================================================================
        # STEP 2: SEO STRATEGIST - Generate campaign options
        # ====================================================================
        step2_start = time.time()
        print(f"[STEP 2/7] SEO Strategist Agent - Generating campaign options...")

        planning_result = orchestrator._step_plan(
            objective=request.campaign_objective,
            tax_dna=tax_dna,
            budget=request.budget
        )

        step2_time = time.time() - step2_start
        step2_output = {
            "agent": "SEO Strategist",
            "status": "complete",
            "timing_seconds": round(step2_time, 2),
            "output": {
                "options_generated": len(planning_result.get("campaign_options", [])),
                "recommendation": planning_result.get("recommendation", {}).get("name", "Unknown")
            }
        }

        # ====================================================================
        # STEP 3: GENERATOR - Create content variations
        # ====================================================================
        step3_start = time.time()
        print(f"[STEP 3/7] Generator Agent - Creating content variations...")

        generation_result = orchestrator._step_generate(
            campaign_option=planning_result.get("recommendation", {}),
            tax_dna=tax_dna
        )

        step3_time = time.time() - step3_start
        step3_output = {
            "agent": "Generator",
            "status": "complete",
            "timing_seconds": round(step3_time, 2),
            "output": {
                "variations_created": generation_result.get("total_variations", 0),
                "channel": generation_result.get("channel", "unknown")
            }
        }

        # ====================================================================
        # STEP 4: EDITOR - Validate compliance
        # ====================================================================
        step4_start = time.time()
        print(f"[STEP 4/7] Editor Agent - Validating compliance...")

        review_result = orchestrator._step_review(
            content=generation_result,
            tax_dna=tax_dna,
            language="es"
        )

        step4_time = time.time() - step4_start
        step4_output = {
            "agent": "Editor",
            "status": "complete",
            "timing_seconds": round(step4_time, 2),
            "output": {
                "is_compliant": review_result.get("is_compliant", False),
                "risk_level": review_result.get("risk_level", "UNKNOWN"),
                "violations": len(review_result.get("violations", []))
            }
        }

        # ====================================================================
        # STEP 5: REPURPOSER - Multi-format transformation
        # ====================================================================
        step5_start = time.time()
        print(f"[STEP 5/7] Repurposer Agent - Transforming to multiple formats...")

        source_content = generation_result.get("variations", [{}])[0].get("contenido", "")
        repurpose_result = orchestrator._step_repurpose(
            source_content=source_content,
            source_type="post",
            target_formats=request.target_channels or ["twitter_thread", "linkedin_post", "instagram_carousel"],
            tax_dna=tax_dna
        )

        step5_time = time.time() - step5_start
        step5_output = {
            "agent": "Repurposer",
            "status": "complete",
            "timing_seconds": round(step5_time, 2),
            "output": {
                "formats_created": repurpose_result.get("total_variations", 0),
                "insights_extracted": len(repurpose_result.get("atomic_insights", [])),
                "reusability_score": repurpose_result.get("reusability_score", 0)
            }
        }

        # ====================================================================
        # STEP 6: ANALYST - Performance analysis (placeholder)
        # ====================================================================
        step6_start = time.time()
        print(f"[STEP 6/7] Analyst Agent - Analyzing performance baseline...")

        # For MVP, analyst runs on empty metrics (would run post-publishing in production)
        analyst_result = {
            "status": "pending",
            "message": "Metrics will be available after publishing"
        }

        step6_time = time.time() - step6_start
        step6_output = {
            "agent": "Analyst",
            "status": "pending",
            "timing_seconds": round(step6_time, 2),
            "output": {
                "message": "Ready to analyze metrics post-publishing"
            }
        }

        # ====================================================================
        # STEP 7: DISTRIBUTION - Schedule publishing (dry-run)
        # ====================================================================
        step7_start = time.time()
        print(f"[STEP 7/7] Distribution Agent - Scheduling publishing (dry-run)...")

        # Prepare posts for distribution
        posts_for_distribution = [
            {
                "id": f"post-{i:03d}",
                "content": var.get("contenido", ""),
                "titulo": var.get("titulo", ""),
                "channel": request.target_channels[0] if request.target_channels else "instagram",
                "scheduled_time": datetime.now().isoformat()
            }
            for i, var in enumerate(generation_result.get("variations", [])[:3], 1)
        ]

        distribution_result = orchestrator._step_distribute(
            posts=posts_for_distribution,
            channels_config={
                "instagram": {"account_id": "placeholder", "access_token": "placeholder"},
                "linkedin": {"org_urn": "placeholder", "access_token": "placeholder"}
            },
            dry_run=not request.execute_distribution
        )

        step7_time = time.time() - step7_start
        step7_output = {
            "agent": "Distribution",
            "status": "complete",
            "timing_seconds": round(step7_time, 2),
            "output": {
                "posts_scheduled": len(distribution_result.get("scheduled", [])),
                "publishing_mode": "dry_run" if not request.execute_distribution else "real"
            }
        }

        # ====================================================================
        # AGGREGATE RESULTS
        # ====================================================================
        pipeline_time = time.time() - pipeline_start

        return {
            "status": "success",
            "workflow_id": f"pipeline-{datetime.now().isoformat()}",
            "total_execution_time_seconds": round(pipeline_time, 2),
            "agent_stages": [
                step1_output,
                step2_output,
                step3_output,
                step4_output,
                step5_output,
                step6_output,
                step7_output
            ],
            "final_output": {
                "tax_dna": tax_dna,
                "campaign_option": planning_result.get("recommendation"),
                "content_variations": len(generation_result.get("variations", [])),
                "compliance_status": review_result.get("is_compliant"),
                "repurposed_formats": repurpose_result.get("total_variations"),
                "publishing_ready": True
            },
            "performance_summary": {
                "fastest_agent": "Distribution",
                "slowest_agent": "Discovery",
                "average_stage_time": round(pipeline_time / 7, 2),
                "target": "<30 seconds"
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Full pipeline execution failed at stage: {str(e)}"
        )


# ============================================================================
# CONTEXIA SERVICES ENDPOINTS (DAY 5)
# ============================================================================

@router.post("/pulso/today", response_model=Dict, tags=["contexia-services"])
async def get_pulso_today(request: PulsoDiariosRequest):
    """
    Get today's Pulso Diario snapshot for a client

    Returns:
        - Tax filings pending
        - Compliance status (traffic light)
        - Active alerts count
        - Audit risk score
        - Revenue status
    """
    try:
        from services.pulso_diario_service import PulsoDiariaService
        service = PulsoDiariaService()
        kpis = service.calculate_daily_kpis(request.company_id)
        return {
            "status": "success",
            "company_id": request.company_id,
            "kpis": kpis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pulso Diario retrieval failed: {sanitize_error_message(str(e))}")


@router.get("/pulso/latest", response_model=Dict, tags=["contexia-services"])
async def get_pulso_latest(company_id: str = Query(..., description="Company ID")):
    """
    Get the most recent Pulso Diario snapshot for a client

    Returns:
        - Latest snapshot with KPIs
        - Snapshot date and time
    """
    try:
        from services.pulso_diario_service import PulsoDiariaService
        service = PulsoDiariaService()
        snapshot = service.get_latest_snapshot(company_id)
        return {
            "status": "success",
            "snapshot": snapshot
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Snapshot retrieval failed: {sanitize_error_message(str(e))}")


@router.post("/centinela/check-risks", response_model=Dict, tags=["contexia-services"])
async def check_centinela_risks(request: CentinelaCheckRequest):
    """
    Check for compliance risks and generate alerts for a client

    Runs comprehensive risk assessment:
    - Compliance profile changes
    - Document expiration dates
    - Audit deadlines
    - Tax return deadlines

    Returns:
        - Alert count by severity
        - List of active alerts with details
    """
    try:
        from services.centinela_fiscal_service import CentinelaFiscalService
        service = CentinelaFiscalService()
        result = service.check_all_risks(request.company_id)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk check failed: {sanitize_error_message(str(e))}")


@router.get("/centinela/alerts", response_model=Dict, tags=["contexia-services"])
async def get_centinela_alerts(company_id: str = Query(..., description="Company ID")):
    """
    Get all active (unresolved) alerts for a client

    Returns:
        - List of active alerts
        - Grouped by severity
    """
    try:
        from services.centinela_fiscal_service import CentinelaFiscalService
        service = CentinelaFiscalService()
        alerts = service.get_active_alerts(company_id)

        # Group by severity
        by_severity = {"critical": [], "warning": [], "info": []}
        for alert in alerts:
            severity = alert.get("severity", "info")
            if severity in by_severity:
                by_severity[severity].append(alert)

        return {
            "status": "success",
            "company_id": company_id,
            "total_alerts": len(alerts),
            "alerts_by_severity": by_severity
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert retrieval failed: {sanitize_error_message(str(e))}")


@router.post("/centinela/acknowledge/{alert_id}", response_model=Dict, tags=["contexia-services"])
async def acknowledge_alert(alert_id: str):
    """
    Acknowledge (mark as reviewed) an alert

    Args:
        alert_id: Alert record ID

    Returns:
        - Success status
        - Updated alert
    """
    try:
        from services.centinela_fiscal_service import CentinelaFiscalService
        service = CentinelaFiscalService()
        success = service.acknowledge_alert(alert_id)
        return {
            "status": "success" if success else "error",
            "alert_id": alert_id,
            "acknowledged": success
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert acknowledgment failed: {sanitize_error_message(str(e))}")


@router.post("/taty/ask", response_model=Dict, tags=["contexia-services"])
async def taty_ask_question(request: TatyQuestionRequest):
    """
    Ask Taty (24/7 assistant) a tax/compliance question

    Provides AI-powered answers to:
    - Tax compliance questions
    - Filing deadlines and requirements
    - Audit-related questions
    - Regulatory requirements

    Args:
        company_id: Client company ID
        question: Question in Spanish or English
        language: Response language (es/en, default: es)

    Returns:
        - AI-generated answer
        - Confidence score (0-1)
        - Conversation ID for tracking
    """
    try:
        from services.taty_rag_service import TatyRagService
        service = TatyRagService()
        answer = service.answer_question(request.company_id, request.question, request.language)
        return answer
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Taty question failed: {sanitize_error_message(str(e))}")


@router.get("/taty/history", response_model=Dict, tags=["contexia-services"])
async def get_taty_history(company_id: str = Query(..., description="Company ID"), limit: int = Query(10, ge=1, le=100)):
    """
    Get conversation history with Taty for a client

    Args:
        company_id: Client company ID
        limit: Number of conversations to retrieve (default 10)

    Returns:
        - List of past conversations
        - Questions asked and answers provided
    """
    try:
        from services.taty_rag_service import TatyRagService
        service = TatyRagService()
        history = service.get_conversation_history(company_id, limit)
        return {
            "status": "success",
            "company_id": company_id,
            "conversation_count": len(history),
            "conversations": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {sanitize_error_message(str(e))}")


@router.get("/taty/faq", response_model=Dict, tags=["contexia-services"])
async def get_taty_faq(language: str = Query("es", description="Language code: es or en")):
    """
    Get frequently asked questions for self-service learning

    Args:
        language: Language code (es/en)

    Returns:
        - List of FAQs
        - Q&A pairs for common questions
    """
    try:
        from services.taty_rag_service import TatyRagService
        service = TatyRagService()
        faqs = service.get_faq(language)
        return {
            "status": "success",
            "language": language,
            "faq_count": len(faqs),
            "faqs": faqs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ retrieval failed: {sanitize_error_message(str(e))}")


@router.post("/orchestrator/full-pipeline-with-persistence", response_model=Dict, tags=["agents"])
async def full_pipeline_with_persistence(request: FullPipelinePersistenceRequest):
    """
    Execute 7-agent pipeline with database persistence to Supabase

    Combines Social Content Ops with campaign persistence:
    1. Execute all 7 agents (Discovery → Distribution)
    2. Save campaign to Supabase
    3. Return workflow ID for tracking

    Args:
        company_url: Company website to analyze
        campaign_objective: Campaign goal
        budget: Campaign budget (default 5000)
        target_channels: Channels to target (instagram, linkedin, facebook, twitter)
        company_id: Optional company ID for attribution
        save_to_db: Save results to Supabase (default True)

    Returns:
        - Complete pipeline results with all 7 agents
        - Database campaign ID (if persisted)
        - Timing per agent stage
    """
    try:
        orchestrator = AgentOrchestrator()
        result = orchestrator.execute_full_pipeline(
            company_url=request.company_url,
            campaign_objective=request.campaign_objective,
            budget=request.budget,
            target_channels=request.target_channels or ["instagram", "linkedin"],
            company_id=request.company_id,
            save_to_db=request.save_to_db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Full pipeline with persistence failed: {str(e)}"
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/orchestrator/health", response_model=Dict, tags=["agents"])
async def health_check():
    """
    Health check for Agent Orchestrator

    Returns:
        - Status (healthy/degraded)
        - Agent availability
        - Database connection status
    """
    try:
        orchestrator = AgentOrchestrator()
        agents = orchestrator.get_all_agents()
        return {
            "status": "healthy",
            "timestamp": orchestrator.created_at,
            "agents_available": len(agents),
            "agents": list(agents.keys())
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }
