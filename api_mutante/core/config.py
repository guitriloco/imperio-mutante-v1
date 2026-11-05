import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env da raiz do projeto imperio_mutante_v1
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "Império Mutante API"
    VERSION: str = "1.0.0"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-2.5-flash")

settings = Settings()
