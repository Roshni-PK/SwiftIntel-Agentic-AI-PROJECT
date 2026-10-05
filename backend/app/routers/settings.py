from fastapi import APIRouter
from backend.app.config import settings
from backend.app.schemas import SettingsResponse, SettingsUpdate
from backend.app.agent.engine import llm_engine

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=SettingsResponse)
def get_settings():
    """Returns application configuration without exposing secrets."""
    status = llm_engine.get_provider_status()
    return SettingsResponse(
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        llm_provider=settings.LLM_PROVIDER,
        model_name=settings.MODEL_NAME,
        api_key_configured=status["is_live_available"],
        demo_mode_active=status["is_demo_mode"],
        database_url=settings.DATABASE_URL,
        chroma_persist_dir=settings.CHROMA_PERSIST_DIR,
        max_critic_retries=settings.MAX_CRITIC_RETRIES
    )

@router.post("", response_model=SettingsResponse)
def update_settings(update: SettingsUpdate):
    """Updates active provider or model parameters in runtime."""
    if update.llm_provider:
        settings.LLM_PROVIDER = update.llm_provider
        llm_engine.provider = update.llm_provider.lower()
    if update.model_name:
        settings.MODEL_NAME = update.model_name
        llm_engine.model_name = update.model_name
    if update.api_key:
        if llm_engine.provider == "openai":
            settings.OPENAI_API_KEY = update.api_key
        elif llm_engine.provider == "groq":
            settings.GROQ_API_KEY = update.api_key
        elif llm_engine.provider == "anthropic":
            settings.ANTHROPIC_API_KEY = update.api_key
        elif llm_engine.provider == "google":
            settings.GOOGLE_API_KEY = update.api_key
            
    llm_engine.is_demo_mode = (
        llm_engine.provider == "demo" or 
        (llm_engine.provider == "openai" and not settings.OPENAI_API_KEY) or
        (llm_engine.provider == "groq" and not settings.GROQ_API_KEY)
    )
    return get_settings()
