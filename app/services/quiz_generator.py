import json
from random import random
import re

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.schemas import QuizGenerationRequest, QuizGenerationResponse


class QuizGeneratorService:
    # Hugging Face Router Endpoint
    HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"

    # Default model with broad provider coverage on the router
    DEFAULT_MODEL = "deepseek-ai/DeepSeek-V3-0324"

    def generate_quiz(self, request: QuizGenerationRequest) -> QuizGenerationResponse:
        headers = {
            "Authorization": f"Bearer {settings.HF_TOKEN}",
            "Content-Type": "application/json",
        }

        # Dynamically switch between uploaded material text or a general topic
        if request.material_text and request.material_text.strip():
            context_prompt = f"Material Text:\n\"\"\"\n{request.material_text}\n\"\"\""
        else:
            context_prompt = f"Topic: {request.topic}"

        system_prompt = """
            You are SABIFY's educational quiz generation engine.

            Your ONLY task is to generate multiple-choice questions about the exact topic or educational material provided by the user.

            STRICT TOPIC RELEVANCE RULE:
            - Every question MUST be directly related to the provided topic.
            - Every answer option MUST be relevant to that question and topic.
            - Every explanation MUST explain the answer using knowledge relevant to that topic.
            - NEVER generate questions about programming, computer science, mathematics, physics, chemistry, biology, history, or any other subject unless that subject is explicitly the provided topic.
            - NEVER substitute your own topic for the user's topic.
            - NEVER introduce an unrelated subject.
            - If the topic is "Biology", generate Biology questions.
            - If the topic is "Programming", generate Programming questions.
            - If the topic is "Newton's Laws of Motion", generate Physics questions specifically about Newton's Laws.
            - If the topic is "Digestive System", generate Biology questions specifically about the digestive system.

            QUALITY RULES:
            - Generate real, accurate educational questions.
            - Every question must have exactly four meaningful answer options.
            - Exactly one option must be correct.
            - The explanation must contain real educational information.
            - Never use placeholder options such as "Option 0", "Option 1", "Option 2", "Option 3", or "string".
            - Return exactly the requested number of questions.

            OUTPUT RULES:
            - Return ONLY valid JSON.
            - Do not return markdown.
            - Do not return ```json.
            - Do not include any text outside the JSON object.

            """

        

        user_prompt = f"""
                Create {request.number_of_questions} multiple-choice questions.

                TARGET EDUCATIONAL TOPIC:
                =========================
                {context_prompt}
                =========================

                The target topic above is the ONLY subject you are allowed to generate questions about.

                Difficulty: {request.difficulty}

                Before generating each question, verify internally:
                1. Is this question directly about the target topic?
                2. Are all four options relevant to the target topic?
                3. Is exactly one option correct?
                4. Does the explanation relate directly to the target topic?

                If a question is unrelated to the target topic, replace it.

                IMPORTANT:
                - Do not change the subject.
                - Do not introduce another subject.
                - Do not generate generic questions.
                - Do not use programming questions unless programming is the target topic.

                Return exactly {request.number_of_questions} questions.

                The JSON MUST follow this structure:

                {{
                    "questions": [
                        {{
                            "question": "A real question about the target topic",
                            "options": [
                                "Option A",
                                "Option B",
                                "Option C",
                                "Option D"
                            ],
                            "correct_answer": 0,
                            "explanation": "Why the correct answer is correct."
                        }}
                    ]
                }}
                """
        payload = {
            "model": self.DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},  # Force JSON mode at HF Router level
            "temperature": 0.1,
            "max_tokens": 3000,
        }

        raw_content = ""

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(self.HF_ROUTER_URL, headers=headers, json=payload)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Hugging Face Router Error: {response.text}",
                )

            data = response.json()
            raw_content = data["choices"][0]["message"]["content"].strip()
            cleaned = self._clean_llm_json(raw_content)
            parsed_data = json.loads(cleaned)

            # Safety fallback: unwrap if the LLM wraps response under keys like "data", "result", or "quiz"
            if isinstance(parsed_data, dict) and "questions" not in parsed_data:
                for key in ["data", "result", "response", "quiz"]:
                    if isinstance(parsed_data.get(key), dict) and "questions" in parsed_data[key]:
                        parsed_data = parsed_data[key]
                        break

            questions = parsed_data.get("questions", [])

            if len(questions) != request.number_of_questions:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AI returned an incorrect number of questions.",
                )

            for question in questions:
                options = question.get("options", [])

                if len(options) != 4:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="AI returned a question without exactly four options.",
                    )

                if any(
                    option.strip().lower() in {
                        "option 0",
                        "option 1",
                        "option 2",
                        "option 3",
                        "string",
                    }
                    for option in options
                ):
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="AI returned placeholder answer options.",
                    )

                if question.get("explanation", "").strip().lower() == "string":
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="AI returned a placeholder explanation.",
                    )

            # Shuffle answer options so the correct answer is not
            # always in the same position.
            for question in questions:
                self._shuffle_question_options(question)

            return QuizGenerationResponse(**parsed_data)

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse LLM JSON output: {str(e)} | Raw: {raw_content}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Network request to Hugging Face failed: {str(e)}",
            )

    @staticmethod
    def _shuffle_question_options(question: dict) -> None:
        """
        Shuffle the answer options while keeping correct_answer
        pointing to the correct option.
        """
        options = question["options"]
        correct_index = question["correct_answer"]

        correct_option = options[correct_index]

        random.shuffle(options)

        question["correct_answer"] = options.index(correct_option)

    @staticmethod
    def _clean_llm_json(raw_content: str) -> str:
        """
        Strip reasoning tokens, markdown fences, and stray leading/trailing text
        around the JSON object.
        """
        content = raw_content

        # Strip DeepSeek-style reasoning chains
        if "</think>" in content:
            content = content.split("</think>")[-1].strip()

        # Strip markdown code fences (```json ... ``` or ``` ... ```)
        if "```" in content:
            match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
            if match:
                content = match.group(1).strip()

        # Fallback: grab the outermost {...} block
        if not content.startswith("{"):
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                content = content[start : end + 1]

        return content.strip()