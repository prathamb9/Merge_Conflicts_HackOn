import os
from pydantic_settings import BaseSettings

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")


class Settings(BaseSettings):
    # LLM API Settings (Groq - Free Tier)
    groq_api_key: str = ""
    # Primary model — fast and token-efficient.
    # llama-3.1-8b-instant has a SEPARATE daily quota from llama-3.3-70b-versatile,
    # so switching here immediately unblocks the app when the 70b daily limit is hit.
    groq_model: str = "llama-3.1-8b-instant"
    # Fallback model tried automatically when the primary is rate-limited.
    groq_fallback_model: str = "gemma2-9b-it"

    # JWT Settings
    secret_key: str = "change-this-secret-key-in-production-make-it-very-long-and-random"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Database Settings (Local SQLite only)
    database_url: str = "sqlite:///./quickcommerce.db"

    # Environment flag
    environment: str = "development"

    # Weather API (optional - for contextual triggers)
    weather_api_key: str = ""
    weather_api_city: str = "Mumbai"

    # Business Rules
    free_delivery_threshold: float = 399.0
    delivery_charge: float = 49.0
    coupon_threshold: float = 499.0
    coupon_discount: float = 75.0

    class Config:
        env_file = env_path
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()
