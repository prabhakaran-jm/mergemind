"""
Configuration management for MergeMind API.
Centralizes environment variable handling and configuration validation.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    environment: str = Field(default="development", env="ENVIRONMENT")
    api_port: int = Field(default=8080, env="API_PORT")
    ui_port: int = Field(default=5173, env="UI_PORT")
    
    # Google Cloud Platform
    gcp_project_id: str = Field(..., env="GCP_PROJECT_ID")
    bq_dataset_raw: str = Field(default="mergemind_raw", env="BQ_DATASET_RAW")
    bq_dataset_modeled: str = Field(default="mergemind", env="BQ_DATASET_MODELED")
    vertex_location: str = Field(default="europe-west2", env="VERTEX_LOCATION")
    
    # GitLab
    gitlab_base_url: str = Field(default="https://35.202.37.189.sslip.io", env="GITLAB_BASE_URL")
    gitlab_token: Optional[str] = Field(default=None, env="GITLAB_TOKEN")
    
    
    # API Configuration
    api_base_url: str = Field(default="http://localhost:8080", env="API_BASE_URL")
    vite_api_base_url: str = Field(default="http://localhost:8080", env="VITE_API_BASE_URL")
    
    # Optional services
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
