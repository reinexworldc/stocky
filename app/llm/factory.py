from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.openrouter import OpenRouterProvider


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "openrouter":
        return OpenRouterProvider()
    raise ValueError(f"Unsupported llm provider: {settings.llm_provider}")
