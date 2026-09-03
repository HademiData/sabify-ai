from fastapi import APIRouter, HTTPException, status
from app.models.schemas import QuizGenerationRequest, QuizGenerationResponse
from app.services.quiz_generator import QuizGeneratorService

router = APIRouter(prefix="/api/v1/quiz", tags=["Quiz"])
quiz_service = QuizGeneratorService()


@router.post("/generate", response_model=QuizGenerationResponse)
async def generate_quiz(request: QuizGenerationRequest):
    # Safe check: ensure material_text OR topic has content
    has_material = request.material_text and request.material_text.strip()
    has_topic = request.topic and request.topic.strip()

    if not has_material and not has_topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'material_text' or 'topic' must be provided."
        )

    try:
        response = quiz_service.generate_quiz(request)
        return response
    except HTTPException:
        # Re-raise explicit HTTPExceptions thrown by the service (400, 503, etc.)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Quiz Generation Failed: {str(e)}"
        )