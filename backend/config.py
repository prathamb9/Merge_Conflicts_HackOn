import os
from pydantic_settings import BaseSettings

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")


class Settings(BaseSettings):
    # LLM API Settings (Groq - Free Tier)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    
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
    
    # Business Rules
    free_delivery_threshold: float = 399.0
    delivery_charge: float = 49.0

    class Config:
        env_file = env_path
        extra = "ignore"
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()
