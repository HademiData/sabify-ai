import json
import random
import re
from typing import Protocol

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.models.schemas import (
    GeneratedQuestion,
    QuizGenerationRequest,
    QuizGenerationResponse,
)
from app.services.huggingface_client import HuggingFaceClient

PLACEHOLDER_OPTIONS = {"option 0", "option 1", "option 2", "option 3", "string"}
RESPONSE_WRAPPERS = ("data", "result", "response", "quiz")


class CompletionClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


SYSTEM_PROMPT = """\
You generate educational multiple-choice quizzes from the user's topic or study
material. Stay strictly within that subject. Write accurate, meaningful questions
with exactly four relevant options, one correct answer, and a useful explanation.
Avoid placeholder text. Return exactly the requested number of questions as a
JSON object with a "questions" array. Each question must contain "question",
"options", "correct_answer" (a zero-based index), and "explanation". Return JSON
only, with no markdown or surrounding text.
"""


class QuizGeneratorService:
    def __init__(self, client: CompletionClient | None = None):
        self.client = client or HuggingFaceClient()

    def generate_quiz(self, request: QuizGenerationRequest) -> QuizGenerationResponse:
        context = self._get_context(request)
        user_prompt = (
            f"Create exactly {request.number_of_questions} multiple-choice "
            f"questions about the subject below.\n\n"
            f"{context}\n\nDifficulty: {request.difficulty}"
        )
        raw_content = self.client.generate(SYSTEM_PROMPT, user_prompt)

        try:
            quiz_data = json.loads(self._clean_llm_json(raw_content))
        except json.JSONDecodeError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The AI service returned invalid quiz data.",
            ) from error

        if isinstance(quiz_data, dict) and "questions" not in quiz_data:
            for key in RESPONSE_WRAPPERS:
                wrapped = quiz_data.get(key)
                if isinstance(wrapped, dict) and "questions" in wrapped:
                    quiz_data = wrapped
                    break

        try:
            quiz = QuizGenerationResponse.model_validate(quiz_data)
        except ValidationError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The AI service returned an invalid quiz.",
            ) from error

        if len(quiz.questions) != request.number_of_questions:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI returned an incorrect number of questions.",
            )

        for question in quiz.questions:
            if any(option.strip().lower() in PLACEHOLDER_OPTIONS for option in question.options):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="AI returned placeholder answer options.",
                )
            if question.explanation.strip().lower() == "string":
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="AI returned a placeholder explanation.",
                )

            self._shuffle_options(question)

        return quiz

    @staticmethod
    def _get_context(request: QuizGenerationRequest) -> str:
        if request.material_text and request.material_text.strip():
            return f"Study material:\n{request.material_text.strip()}"
        return f"Topic: {request.topic.strip() if request.topic else ''}"

    @staticmethod
    def _shuffle_options(question: GeneratedQuestion) -> None:
        options = list(enumerate(question.options))
        random.shuffle(options)
        question.options = [option for _, option in options]
        question.correct_answer = next(
            index
            for index, (original_index, _) in enumerate(options)
            if original_index == question.correct_answer
        )

    @staticmethod
    def _clean_llm_json(raw_content: str) -> str:
        content = raw_content
        if "</think>" in content:
            content = content.rsplit("</think>", 1)[-1].strip()

        match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
        if match:
            content = match.group(1).strip()

        if not content.startswith("{"):
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end > start:
                content = content[start : end + 1]

        return content.strip()
