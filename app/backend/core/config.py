import os
from pydantic import BaseModel

class Settings(BaseModel):
    # External LLM provider
    AIMLAPI_BASE_URL: str = os.getenv("AIMLAPI_BASE_URL", "https://api.aimlapi.com/v1")
    AIMLAPI_API_KEY: str | None = os.getenv("AIMLAPI_API_KEY")

    # Models
    SMOL_MODEL: str = os.getenv("SMOL_MODEL", "testgpt-5-nano-2025-08-07")
    CHEAP_MODEL: str = os.getenv("CHEAP_MODEL", "testgpt-5-nano-2025-08-07")
    MAIN_MODEL: str = os.getenv("MAIN_MODEL", "gpt-5-chat-latest")

    # Server
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8080"))

    def env_summary(self) -> dict:
        return {
            "SMOL_MODEL": self.SMOL_MODEL,
            "CHEAP_MODEL": self.CHEAP_MODEL,
            "MAIN_MODEL": self.MAIN_MODEL,
            "base_url": self.AIMLAPI_BASE_URL,
            "has_api_key": bool(self.AIMLAPI_API_KEY),
        }

settings = Settings()
