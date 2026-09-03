from typing import List, Optional
from pydantic import BaseModel, Field

class QuizGenerationRequest(BaseModel):

    # Optional fields - no longer required by the endpoint
    course_id: Optional[str] = None
    material_id: Optional[str] = None
    material_text: Optional[str] = None
    
    # New optional topic field if generating without uploaded material
    topic: Optional[str] = None
    
    # Required generation settings
    number_of_questions: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="basic")
    question_type: str = Field(default="multiple_choice")

class GeneratedQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int = Field(description="Zero-based index of the correct option")
    explanation: str

class QuizGenerationResponse(BaseModel):
    questions: List[GeneratedQuestion]