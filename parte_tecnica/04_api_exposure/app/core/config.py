"""
Configuration management for Steel Price Predictor API
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    app_name: str = "Steel Rebar Price Predictor"
    app_version: str = "v2.0"
    debug: bool = False
    
    # GCP
    project_id: str = "cdo-yacosta"
    region: str = "us-central1"
    
    # Storage
    model_bucket: str = "cdo-yacosta-models"
    model_path: str = "models/TWO_STAGE_MODEL.pkl"
    prediction_cache_path: str = "predictions/current.json"
    
    # Prediction defaults (emergency fallback only)
    default_prediction_price: float = 941.0  # Retail Sep 2025 avg
    
    # Firestore
    firestore_database: str = "(default)"
    rate_limit_collection: str = "rate_limits"
    
    # Secret Manager
    api_keys_secret: str = "steel-predictor-api-keys"
    
    # API Configuration
    rate_limit_requests: int = 100  # Per hour
    rate_limit_window_seconds: int = 3600  # 1 hour
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # Prediction
    default_confidence: float = 0.95
    wholesale_discount: float = 0.8874  # Minorista → Mayorista
    
    # CORS
    cors_origins: List[str] = ["*"]  # Allow all for testing
    
    # Logging
    log_level: str = "INFO"
    
    # Model Metadata
    data_sources: List[str] = ["LME", "Banxico", "EPU", "Trade Events"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
