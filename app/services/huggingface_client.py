import logging

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


class HuggingFaceClient:
    endpoint = "https://router.huggingface.co/v1/chat/completions"
    timeout = 60.0

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not settings.HF_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Hugging Face API token is not configured.",
            )

        payload = {
            "model": settings.HF_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 3000,
        }
        headers = {
            "Authorization": f"Bearer {settings.HF_TOKEN}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.endpoint, headers=headers, json=payload)
        except httpx.RequestError as error:
            logger.error("Hugging Face request failed: %s", error)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI quiz service is currently unavailable. Please try again later.",
            ) from error

        if response.status_code != status.HTTP_200_OK:
            logger.error(
                "Hugging Face returned status %s: %s",
                response.status_code,
                response.text,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI quiz service is currently unavailable. Please try again later.",
            )

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as error:
            logger.error("Hugging Face returned an invalid completion response: %s", error)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The AI service returned an invalid response.",
            ) from error

        if not isinstance(content, str) or not content.strip():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The AI service returned an empty response.",
            )

        return content.strip()
