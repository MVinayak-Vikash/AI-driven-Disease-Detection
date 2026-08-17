import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "AI Early-Risk & Referral Navigator"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,*"

    # Supabase Configuration
    SUPABASE_URL: str = "https://placeholder.supabase.co"
    SUPABASE_ANON_KEY: str = "placeholder-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "placeholder-service-role-key"
    SUPABASE_JWT_SECRET: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    # AI Configuration
    # Options: 'mock', 'base', 'finetuned'
    AI_PROVIDER: str = "mock"
    MODEL_NAME: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    MODEL_BASE_URL: Optional[str] = "https://api.together.xyz/v1"
    MODEL_API_KEY: Optional[str] = None
    UNSLOTH_MODEL_PATH: Optional[str] = "./llm/checkpoints/cardionav-unsloth-lora"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origin_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
