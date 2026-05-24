from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class TatyQuestion(BaseModel):
    company_id: str
    question: str
    language: str = "es"


class TatyResponse(BaseModel):
    company_id: str
    question: str
    answer: str
    confidence: float
    sources: list = []


@router.post("/ask")
async def taty_ask(request: TatyQuestion):
    """
    POST /api/v1/taty/ask
    Request: { "company_id": "...", "question": "...", "language": "es" }
    Response: Q&A with fiscal/accounting answer

    RAG Assistant for tax & accounting questions (Spanish)
    """
    company_id = request.company_id
    question = request.question

    # Demo response - in production would use RAG + pgvector
    demo_answers = {
        "vencimiento": "La declaración de renta 2025 vence el 10 de abril de 2026 para personas naturales.",
        "iva": "El IVA se declara mensualmente o bimestralmente según tu régimen.",
        "retenciones": "Las retenciones en la fuente deben pagarse entre el 1-3 del mes siguiente.",
        "default": "Para consultas específicas sobre impuestos, contacta con tu asesor fiscal."
    }

    # Simple keyword matching for demo
    answer_key = "default"
    for key in demo_answers.keys():
        if key in question.lower():
            answer_key = key
            break

    return TatyResponse(
        company_id=company_id,
        question=question,
        answer=demo_answers[answer_key],
        confidence=0.85,
        sources=["DIAN", "Regulación Tributaria Colombiana"]
    )
