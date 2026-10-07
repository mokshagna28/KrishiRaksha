"""
KRISHIRAKSHA AI - Pydantic Request & Response Schemas
Student Roll Number: 231FA04291
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re

# ==============================================================================
# Auth Schemas
# ==============================================================================
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# ==============================================================================
# Farmer Schemas
# ==============================================================================
class FarmerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    mobile_number: str = Field(..., description="Indian 10-digit mobile or with +91")
    state_id: int
    district_id: int
    mandal_block: Optional[str] = None
    preferred_language: str = "English"
    crop: str = Field(..., min_length=2, max_length=100)
    crop_stage: str = Field(..., min_length=2, max_length=50)

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        # Standardize Indian mobile number to +91XXXXXXXXXX
        cleaned = re.sub(r"[^\d+]", "", v)
        if cleaned.startswith("+91") and len(cleaned) == 13:
            return cleaned
        elif cleaned.startswith("91") and len(cleaned) == 12:
            return "+" + cleaned
        elif len(cleaned) == 10 and cleaned[0] in "6789":
            return "+91" + cleaned
        raise ValueError("Invalid Indian mobile number format. Must be a valid 10-digit number.")

class FarmerCreate(FarmerBase):
    pass

class FarmerUpdate(BaseModel):
    full_name: Optional[str] = None
    mandal_block: Optional[str] = None
    preferred_language: Optional[str] = None
    crop: Optional[str] = None
    crop_stage: Optional[str] = None
    is_active: Optional[bool] = None

class FarmerOut(BaseModel):
    id: int
    full_name: str
    mobile_number_masked: str
    state_id: int
    state_name: str
    district_id: int
    district_name: str
    mandal_block: Optional[str]
    preferred_language: str
    crop: str
    crop_stage: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ==============================================================================
# State & District Schemas
# ==============================================================================
class DistrictBrief(BaseModel):
    id: int
    state_id: int
    code: str
    name: str
    latitude: float
    longitude: float
    current_risk: str = "LOW"
    official_warning: str = "GREEN"
    current_rainfall: float = 0.0
    forecast_rainfall: float = 0.0
    risk_score: float = 0.0

class StateBrief(BaseModel):
    id: int
    code: str
    name: str
    latitude: float
    longitude: float
    default_language: str
    current_risk: str = "LOW"
    official_warning: str = "GREEN"
    affected_districts_count: int = 0
    total_farmers: int = 0
    total_alerts: int = 0

class DistrictDetail(BaseModel):
    id: int
    name: str
    state_name: str
    state_id: int
    latitude: float
    longitude: float
    current_rainfall: float # mm
    forecast_rainfall_24h: float # mm
    forecast_rainfall_48h: float # mm
    recent_accumulated_7d: float # mm
    temperature: Optional[float]
    humidity: Optional[float]
    wind_speed: Optional[float]
    official_warning: str # GREEN, YELLOW, ORANGE, RED
    ai_risk: str # LOW, MODERATE, HIGH, VERY_HIGH
    risk_score: float # 0-100
    prediction_confidence: float # %
    risk_reasons: List[str]
    data_freshness: str
    last_updated: datetime
    active_farmers_count: int

# ==============================================================================
# Risk & Warning Schemas
# ==============================================================================
class RiskAssessmentOut(BaseModel):
    district_id: int
    district_name: str
    state_name: str
    ai_risk_level: str
    official_warning_level: str
    final_risk_level: str
    risk_score: float
    confidence: float
    contributing_factors: List[str]
    data_freshness_status: str
    assessment_time: datetime

# ==============================================================================
# Alert Schemas
# ==============================================================================
class AlertOut(BaseModel):
    id: int
    alert_fingerprint: str
    state_id: int
    state_name: str
    district_id: int
    district_name: str
    risk_level: str
    official_warning: str
    forecast_period: str
    headline: str
    description_en: str
    created_at: datetime
    status: str
    recipients_count: int = 0

class SimulateAlertRequest(BaseModel):
    state_id: int
    district_id: int
    risk_level: str = "HIGH" # HIGH, VERY_HIGH
    language: Optional[str] = None
    custom_note: Optional[str] = None
    send_sms: bool = False # If true, dispatches according to SMS_MODE

class SimulateAlertPreview(BaseModel):
    state_name: str
    district_name: str
    risk_level: str
    affected_farmers_count: int
    language_breakdown: Dict[str, int]
    templates_preview: Dict[str, str]
    sms_mode: str

# ==============================================================================
# SMS Schemas
# ==============================================================================
class TestSmsRequest(BaseModel):
    mobile_number: str
    language: str = "English"
    state_name: str = "Andhra Pradesh"
    district_name: str = "Guntur"
    period: str = "Next 24-48 Hours"

class TestSmsResponse(BaseModel):
    status: str
    provider: str
    sms_mode: str
    message: str
    provider_response: Dict[str, Any]
    dlt_template_id: Optional[str]

class SmsMessageOut(BaseModel):
    id: int
    farmer_id: int
    farmer_name: str
    mobile_masked: str
    alert_id: Optional[int]
    language: str
    template_id: Optional[str]
    provider: str
    provider_message_id: Optional[str]
    submitted_at: datetime
    delivered_at: Optional[datetime]
    status: str
    failure_reason: Optional[str]

class DltConfigStatus(BaseModel):
    sms_mode: str # "demo" or "live"
    dlt_registered: bool
    sender_id_configured: bool
    sender_id: Optional[str]
    msg91_auth_configured: bool
    templates_configured: Dict[str, bool]
    gateway_status: str # "READY", "DEMO_MODE", "NOT_CONFIGURED"

# ==============================================================================
# ML Model & Evaluation Schemas
# ==============================================================================
class MLMetricsOut(BaseModel):
    model_name: str
    model_version: str
    algorithm: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    training_dataset_size: int
    test_dataset_size: int
    training_period: str
    data_source: str
    trained_at: datetime
    is_active: bool
    confusion_matrix: List[List[int]]
    feature_importance: Dict[str, float]
    distinction_note: str

# ==============================================================================
# System Diagnostics Schemas
# ==============================================================================
class SystemStatusSummary(BaseModel):
    weather_api: str # "CONNECTED" or "ERROR"
    database: str # "CONNECTED" or "ERROR"
    ml_model: str # "READY" or "ERROR"
    mlflow: str # "CONNECTED" or "ERROR"
    sms_gateway: str # "CONFIGURED", "DEMO_MODE", "NOT CONFIGURED"
    dlt: str # "CONFIGURED" or "NOT CONFIGURED"
    last_weather_update: Optional[datetime]
    last_prediction_update: Optional[datetime]
    total_states_monitored: int
    total_districts_monitored: int
    low_risk_count: int
    moderate_risk_count: int
    high_risk_count: int
    very_high_risk_count: int
    official_warnings_count: int
    active_farmers_count: int
    alerts_today: int
    timestamp: datetime
