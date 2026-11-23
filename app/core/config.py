import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    HF_MODEL: str = os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-V3-0324")
    PORT: int = int(os.getenv("PORT", 8082))


settings = Settings()
