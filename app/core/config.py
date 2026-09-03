import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    HF_MODEL: str = os.getenv("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct")
    PORT: int = int(os.getenv("PORT", 8082))
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

settings = Settings()
