import json
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.models.schemas import QuizGenerationRequest
from app.services.quiz_generator import QuizGeneratorService


class FakeClient:
    def __init__(self, content: str):
        self.content = content

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return self.content


def quiz_response(**question_overrides: object) -> str:
    question = {
        "question": "Which option is correct?",
        "options": ["A", "B", "C", "D"],
        "correct_answer": 2,
        "explanation": "C is correct.",
        **question_overrides,
    }
    return json.dumps({"questions": [question]})


class QuizGeneratorTests(unittest.TestCase):
    def test_shuffling_preserves_correct_answer(self):
        service = QuizGeneratorService(FakeClient(quiz_response()))
        request = QuizGenerationRequest(topic="Testing", number_of_questions=1)

        with patch(
            "app.services.quiz_generator.random.shuffle",
            side_effect=lambda options: options.reverse(),
        ):
            quiz = service.generate_quiz(request)

        question = quiz.questions[0]
        self.assertEqual(question.options[question.correct_answer], "C")

    def test_rejects_response_with_wrong_question_count(self):
        service = QuizGeneratorService(FakeClient(quiz_response()))
        request = QuizGenerationRequest(topic="Testing", number_of_questions=2)

        with self.assertRaises(HTTPException) as error:
            service.generate_quiz(request)

        self.assertEqual(error.exception.status_code, 502)

    def test_rejects_invalid_option_count(self):
        service = QuizGeneratorService(FakeClient(quiz_response(options=["A", "B"])))
        request = QuizGenerationRequest(topic="Testing", number_of_questions=1)

        with self.assertRaises(HTTPException) as error:
            service.generate_quiz(request)

        self.assertEqual(error.exception.status_code, 502)


if __name__ == "__main__":
    unittest.main()
