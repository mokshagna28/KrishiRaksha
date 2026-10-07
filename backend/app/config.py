"""
KRISHIRAKSHA AI - Configuration Management
Student Roll Number: 231FA04291
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # Core Application Info
    PROJECT_NAME: str = "KRISHIRAKSHA AI"
    PROJECT_TITLE: str = "AI-Based Heavy Rainfall & Flood Risk Early Warning System for Indian Farmers"
    STUDENT_ROLL_NUMBER: str = "231FA04291"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Security & JWT Auth
    SECRET_KEY: str = "krishiraksha-super-secret-key-231fa04291-btech-final-project-secure-token"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ADMIN_DEFAULT_USERNAME: str = "admin"
    ADMIN_DEFAULT_PASSWORD: str = "AdminPassword@231FA"
    ADMIN_DEFAULT_EMAIL: str = "admin@krishiraksha.in"

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./krishiraksha.db"

    # Weather Source & IMD Configuration
    WEATHER_PROVIDER: str = "IMD"
    IMD_API_BASE_URL: str = "https://mausam.imd.gov.in/api"
    IMD_BACKUP_API_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_CACHE_TTL_MINUTES: int = 30
    WEATHER_UPDATE_INTERVAL_MINUTES: int = 60
    WEATHER_REQUEST_TIMEOUT_SECONDS: int = 15
    WEATHER_MAX_RETRIES: int = 3

    # Machine Learning & MLOps
    MLFLOW_TRACKING_URI: str = "sqlite:///./mlruns.db"
    MLFLOW_EXPERIMENT_NAME: str = "Rainfall_Flood_Risk_MLOps_231FA04291"
    MODEL_REGISTRY_NAME: str = "HeavyRainRiskModel_231FA04291"
    ML_MODEL_TYPE: str = "RandomForest"
    MODEL_ARTIFACTS_DIR: str = "ml_artifacts"

    # SMS Gateway (MSG91) Configuration
    # Modes: 'demo' (safe simulation for evaluation/testing) or 'live' (real Indian SMS)
    SMS_MODE: str = "demo"
    MSG91_AUTH_KEY: Optional[str] = None
    MSG91_SENDER_ID: Optional[str] = None
    MSG91_ROUTE: str = "4"

    # DLT Template IDs for Supported Indian Languages
    MSG91_TEMPLATE_ID_EN: Optional[str] = None
    MSG91_TEMPLATE_ID_TE: Optional[str] = None
    MSG91_TEMPLATE_ID_HI: Optional[str] = None
    MSG91_TEMPLATE_ID_TA: Optional[str] = None
    MSG91_TEMPLATE_ID_KN: Optional[str] = None
    MSG91_TEMPLATE_ID_ML: Optional[str] = None
    MSG91_TEMPLATE_ID_MR: Optional[str] = None
    MSG91_TEMPLATE_ID_BN: Optional[str] = None
    MSG91_TEMPLATE_ID_OR: Optional[str] = None
    MSG91_TEMPLATE_ID_GU: Optional[str] = None
    MSG91_TEMPLATE_ID_PA: Optional[str] = None

    # Redis & Background Tasks
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
