from fastapi import APIRouter, HTTPException, status

from app.models.schemas import QuizGenerationRequest, QuizGenerationResponse
from app.services.quiz_generator import QuizGeneratorService

router = APIRouter(prefix="/api/v1/quiz", tags=["Quiz"])
quiz_service = QuizGeneratorService()


@router.post("/generate", response_model=QuizGenerationResponse)
def generate_quiz(request: QuizGenerationRequest) -> QuizGenerationResponse:
    has_topic = bool(request.topic and request.topic.strip())
    has_material = bool(request.material_text and request.material_text.strip())
    if not (has_topic or has_material):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'material_text' or 'topic' must be provided.",
        )

    return quiz_service.generate_quiz(request)