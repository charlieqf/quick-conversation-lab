"""
Application configuration using pydantic-settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str = ""
    openai_api_key: str = ""
    
    # Google Cloud
    gcp_project_id: str = ""
    gcs_bucket_name: str = "voice-model-lab"
    
    # Server
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    debug: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
