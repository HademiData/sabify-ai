from pydantic import BaseModel, Field


class QuizGenerationRequest(BaseModel):
    course_id: str | None = None
    material_id: str | None = None
    material_text: str | None = None
    topic: str | None = None
    number_of_questions: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="basic")
    question_type: str = Field(default="multiple_choice")


class GeneratedQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: int = Field(ge=0, le=3, description="Zero-based index of the correct option")
    explanation: str


class QuizGenerationResponse(BaseModel):
    questions: list[GeneratedQuestion]