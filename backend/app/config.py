"""
Application configuration using pydantic-settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from typing import List, Optional # Added Optional import
import os


class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str = ""
    openai_api_key: str = ""
    xai_api_key: str = ""
    dashscope_api_key: str = ""
    volc_api_key: str = "" # Legacy / Ark API Key
    volc_access_key: str = "" # From Speech Console (the Token)
    volc_secret_key: str = "" # From Speech Console
    volc_app_id: str = "" # From Speech Console
    
    # Google Cloud
    gcp_project_id: str = ""
    gcs_bucket_name: str = "voice-model-lab"
    
    # Server
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://quick-conversation-lab.web.app",
        "https://quick-conversation-lab.firebaseapp.com"
    ]
    debug: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
