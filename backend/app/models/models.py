"""
KRISHIRAKSHA AI - Database Models Schema
Student Roll Number: 231FA04291
Fully relational architecture with indexes, constraints, and audit trails.
"""

import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

class State(Base):
    __tablename__ = "states"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True) # e.g. "AP", "MH", "KL"
    name = Column(String(100), unique=True, nullable=False, index=True) # e.g. "Andhra Pradesh"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    default_language = Column(String(20), default="English", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    districts = relationship("District", back_populates="state", cascade="all, delete-orphan")
    farmers = relationship("Farmer", back_populates="state")
    alerts = relationship("Alert", back_populates="state")

class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    state_id = Column(Integer, ForeignKey("states.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(20), nullable=False) # e.g. "GNT", "KRI"
    name = Column(String(100), nullable=False, index=True) # e.g. "Guntur"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    state = relationship("State", back_populates="districts")
    farmers = relationship("Farmer", back_populates="district")
    weather_observations = relationship("WeatherObservation", back_populates="district", cascade="all, delete-orphan")
    weather_forecasts = relationship("WeatherForecast", back_populates="district", cascade="all, delete-orphan")
    official_warnings = relationship("OfficialWarning", back_populates="district", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="district", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="district", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="district")

    __table_args__ = (
        Index("idx_district_state_name", "state_id", "name"),
    )

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    mobile_number = Column(String(15), unique=True, nullable=False, index=True) # E.164 e.g. "+919876543210"
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    mandal_block = Column(String(100), nullable=True)
    preferred_language = Column(String(20), default="English", nullable=False) # English, Hindi, Telugu, etc.
    crop = Column(String(100), nullable=False) # e.g. "Paddy", "Cotton", "Chilli"
    crop_stage = Column(String(50), nullable=False) # "Sowing", "Vegetative", "Flowering", "Harvesting"
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    state = relationship("State", back_populates="farmers")
    district = relationship("District", back_populates="farmers")
    sms_messages = relationship("SmsMessage", back_populates="farmer")

    __table_args__ = (
        Index("idx_farmer_target", "state_id", "district_id", "is_active", "preferred_language"),
    )

class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), default="IMD", nullable=False) # "IMD", "IMD_API_BACKUP"
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    observation_time = Column(DateTime, nullable=False, index=True)
    forecast_time = Column(DateTime, nullable=True)
    rainfall = Column(Float, default=0.0, nullable=False) # mm in last 24h
    temperature = Column(Float, nullable=True) # Celsius
    humidity = Column(Float, nullable=True) # Relative %
    wind_speed = Column(Float, nullable=True) # km/h
    warning_code = Column(String(20), nullable=True) # e.g. "HEAVY_RAIN"
    warning_color = Column(String(20), default="GREEN", nullable=False) # GREEN, YELLOW, ORANGE, RED
    raw_response_hash = Column(String(64), nullable=True) # SHA-256 hash of raw provider response
    retrieved_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    # Relationships
    district = relationship("District", back_populates="weather_observations")

    __table_args__ = (
        Index("idx_obs_district_retrieved", "district_id", "retrieved_at"),
    )

class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), default="IMD", nullable=False)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    forecast_time = Column(DateTime, nullable=False, index=True)
    expected_rainfall_24h = Column(Float, default=0.0, nullable=False) # mm expected next 24h
    expected_rainfall_48h = Column(Float, default=0.0, nullable=False) # mm expected next 48h
    temperature = Column(Float, nullable=True)
    warning_color = Column(String(20), default="GREEN", nullable=False) # IMD Forecast Color
    retrieved_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    district = relationship("District", back_populates="weather_forecasts")

class OfficialWarning(Base):
    __tablename__ = "official_warnings"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), default="IMD", nullable=False)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    warning_level = Column(String(50), nullable=False) # "NO_WARNING", "WATCH", "ALERT", "WARNING"
    warning_color = Column(String(20), default="GREEN", nullable=False) # GREEN, YELLOW, ORANGE, RED
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)
    retrieved_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    district = relationship("District", back_populates="official_warnings")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    features_version = Column(String(50), default="v1.0", nullable=False)
    prediction_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    heavy_rain_prob = Column(Float, nullable=False) # ML Probability between 0.0 and 1.0
    predicted_class = Column(Integer, nullable=False) # 0 = Normal, 1 = Heavy Rain Risk
    confidence = Column(Float, nullable=False) # Probability confidence %
    input_features = Column(Text, nullable=True) # JSON encoded features dictionary

    district = relationship("District", back_populates="predictions")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    assessment_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    ai_risk_level = Column(String(20), nullable=False) # LOW, MODERATE, HIGH, VERY_HIGH
    official_warning_level = Column(String(20), nullable=False) # GREEN, YELLOW, ORANGE, RED
    final_risk_level = Column(String(20), nullable=False, index=True) # LOW, MODERATE, HIGH, VERY_HIGH
    risk_score = Column(Float, nullable=False) # 0 - 100 composite index
    confidence = Column(Float, nullable=False) # %
    contributing_factors = Column(Text, nullable=False) # JSON array of validated real reasons
    data_freshness_status = Column(String(50), default="FRESH", nullable=False) # FRESH, CACHED, STALE, DATA_INSUFFICIENT

    district = relationship("District", back_populates="risk_assessments")

    __table_args__ = (
        Index("idx_risk_district_time", "district_id", "assessment_time"),
    )

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_fingerprint = Column(String(128), unique=True, nullable=False, index=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    risk_level = Column(String(20), nullable=False, index=True) # HIGH, VERY_HIGH
    official_warning = Column(String(20), nullable=False) # ORANGE, RED
    forecast_period = Column(String(50), default="Next 24-48 Hours", nullable=False)
    headline = Column(String(200), nullable=False)
    description_en = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    status = Column(String(20), default="ACTIVE", nullable=False) # ACTIVE, UPGRADED, RESOLVED

    # Relationships
    state = relationship("State", back_populates="alerts")
    district = relationship("District", back_populates="alerts")
    sms_messages = relationship("SmsMessage", back_populates="alert")

    __table_args__ = (
        Index("idx_alert_lookup", "district_id", "status", "created_at"),
    )

class SmsMessage(Base):
    __tablename__ = "sms_messages"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True, index=True)
    language = Column(String(20), nullable=False)
    template_id = Column(String(50), nullable=True)
    provider = Column(String(50), default="MSG91", nullable=False)
    provider_message_id = Column(String(100), nullable=True)
    mobile_masked = Column(String(20), nullable=False) # e.g. +91******3210
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    delivered_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="QUEUED", nullable=False, index=True) # QUEUED, SUBMITTED, DELIVERED, FAILED, UNKNOWN
    failure_reason = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True) # Message content or template variables

    farmer = relationship("Farmer", back_populates="sms_messages")
    alert = relationship("Alert", back_populates="sms_messages")

    __table_args__ = (
        Index("idx_sms_status_time", "status", "submitted_at"),
    )

class SmsTemplate(Base):
    __tablename__ = "sms_templates"

    id = Column(Integer, primary_key=True, index=True)
    language = Column(String(20), unique=True, nullable=False, index=True)
    template_name = Column(String(100), nullable=False)
    dlt_template_id = Column(String(50), nullable=True)
    content_pattern = Column(Text, nullable=False) # Template text with {{district}}, {{state}}, {{period}}
    is_active = Column(Boolean, default=True, nullable=False)

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    algorithm = Column(String(50), nullable=False)
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=False)
    trained_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    artifact_path = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    component = Column(String(50), nullable=False, index=True) # "WEATHER_API", "ML_ENGINE", "SMS_GATEWAY", "SCHEDULER"
    level = Column(String(20), default="INFO", nullable=False) # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(20), default="ADMIN", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ══════════════════════════════════════════════════════════════════════════
# EXTENSION 2 — MARKETPLACE & CROP PRICE FORECASTING MODELS
# ══════════════════════════════════════════════════════════════════════════
class CropListing(Base):
    __tablename__ = "crop_listings"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False, index=True)
    crop = Column(String(100), nullable=False, index=True)
    variety = Column(String(100), nullable=True)
    quantity = Column(Float, nullable=False)
    quantity_unit = Column(String(20), default="kg", nullable=False) # "kg", "quintal", "ton"
    quality = Column(String(50), default="Grade A", nullable=False) # "Grade A", "Grade B", "Organic", "FAQ"
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    village = Column(String(100), nullable=True)
    expected_price = Column(Float, nullable=False) # Farmer asking price per unit
    available_from = Column(DateTime, nullable=False)
    harvest_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    status = Column(String(20), default="ACTIVE", nullable=False, index=True) # ACTIVE, SOLD, EXPIRED, CANCELLED
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    farmer = relationship("Farmer")
    purchase_requests = relationship("PurchaseRequest", back_populates="listing", cascade="all, delete-orphan")


class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    mobile_or_email = Column(String(100), unique=True, nullable=False, index=True)
    organization = Column(String(150), nullable=True) # e.g. "Sri Lakshmi Agro Traders", "Retail Wholesale Co."
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    purchase_requests = relationship("PurchaseRequest", back_populates="buyer")


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("crop_listings.id"), nullable=False, index=True)
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=False, index=True)
    requested_quantity = Column(Float, nullable=False)
    offered_price = Column(Float, nullable=False) # Price offered per unit
    message = Column(Text, nullable=True)
    status = Column(String(20), default="REQUESTED", nullable=False, index=True) # REQUESTED, ACCEPTED, REJECTED, NEGOTIATING, CONFIRMED, COMPLETED, CANCELLED
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    listing = relationship("CropListing", back_populates="purchase_requests")
    buyer = relationship("Buyer", back_populates="purchase_requests")


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    market = Column(String(100), nullable=False, index=True)
    crop = Column(String(100), nullable=False, index=True)
    variety = Column(String(100), nullable=True)
    grade = Column(String(50), nullable=True)
    min_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    modal_price = Column(Float, nullable=False)
    price_unit = Column(String(20), default="₹/quintal", nullable=False)
    arrivals = Column(Float, nullable=True) # Quintals
    source = Column(String(100), default="AGMARKNET / eNAM", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class PricePrediction(Base):
    __tablename__ = "price_predictions"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(100), nullable=False, index=True)
    market = Column(String(100), nullable=False, index=True)
    prediction_date = Column(DateTime, nullable=False, index=True)
    forecast_date = Column(DateTime, nullable=False, index=True)
    predicted_price = Column(Float, nullable=False)
    price_unit = Column(String(20), default="₹/kg", nullable=False)
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class SellingRecommendation(Base):
    __tablename__ = "selling_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(100), nullable=False, index=True)
    market = Column(String(100), nullable=False, index=True)
    current_price = Column(Float, nullable=False)
    forecast_period_days = Column(Integer, default=7, nullable=False)
    predicted_best_date = Column(String(20), nullable=False)
    predicted_best_price = Column(Float, nullable=False)
    recommendation = Column(String(50), nullable=False) # FAVORABLE_TO_SELL, WAIT_AND_MONITOR, LOWER_PRICE_EXPECTED
    price_change_pct = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
