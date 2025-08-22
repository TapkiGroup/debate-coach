import os
from pydantic import BaseModel

class Settings(BaseModel):
    # External LLM provider
    AIMLAPI_BASE_URL: str = os.getenv("AIML_BASE_URL")
    AIMLAPI_API_KEY: str | None = os.getenv("AIML_API_KEY")
    # External search provider
    TAVILY_API_KEY: str | None = os.getenv("TAVILY_API_KEY")  

    # Models
    SMOL_MODEL: str = os.getenv("AIML_MODEL_NANO")
    CHEAP_MODEL: str = os.getenv("AIML_MODEL_NANO")
    MAIN_MODEL: str = os.getenv("AIML_MODEL_HEAVY")

    # Server
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("PORT", os.getenv("APP_PORT", "8080")))

    def env_summary(self) -> dict:
        return {
            "SMOL_MODEL": self.SMOL_MODEL,
            "CHEAP_MODEL": self.CHEAP_MODEL,
            "MAIN_MODEL": self.MAIN_MODEL,
            "base_url": self.AIMLAPI_BASE_URL,
            "has_api_key": bool(self.AIMLAPI_API_KEY),
        }

settings = Settings()
