import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "SwiftIntel"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "demo")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "demo-engine")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Storage Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'detectiveai.db'}")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))
    EVIDENCE_UPLOAD_DIR: str = os.getenv("EVIDENCE_UPLOAD_DIR", str(BASE_DIR / "uploads" / "evidence"))
    AUTH_COOKIE_SECURE: bool = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
    
    # Investigation limits
    MAX_CRITIC_RETRIES: int = int(os.getenv("MAX_CRITIC_RETRIES", "2"))
    
    class Config:
        env_file = str(PROJECT_DIR / ".env")
        extra = "ignore"

settings = Settings()
