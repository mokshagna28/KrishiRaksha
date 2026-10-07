"""
KRISHIRAKSHA AI - FastAPI Application
Student Roll Number: 231FA04291
AI-Based Heavy Rainfall & Flood Risk Early Warning System for Indian Farmers
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from backend.app.config import settings
from backend.app.database import engine, get_db, Base
from backend.app.models.models import (
    State, District, Farmer, WeatherObservation, WeatherForecast,
    OfficialWarning, Prediction, RiskAssessment, Alert, SmsMessage,
    SmsTemplate, ModelVersion, SystemLog, AdminUser
)
from backend.app.schemas.schemas import (
    Token, LoginRequest, FarmerCreate, FarmerUpdate, FarmerOut,
    StateBrief, DistrictBrief, DistrictDetail, RiskAssessmentOut,
    AlertOut, SimulateAlertRequest, SimulateAlertPreview,
    TestSmsRequest, TestSmsResponse, SmsMessageOut, DltConfigStatus,
    MLMetricsOut, SystemStatusSummary
)
from backend.app.core.security import (
    verify_password, create_access_token, get_current_admin, get_password_hash
)
from backend.app.services.weather.imd_client import imd_client
from backend.app.services.language_service import language_service, SUPPORTED_LANGUAGES
from backend.app.services.sms.msg91_service import msg91_service
from backend.app.services.risk_engine import risk_engine
from backend.app.services.alert_service import alert_service
from backend.ml.predict import predict_heavy_rain_risk
from backend.ml.model_registry import model_registry
from backend.ml.crop_water.predict import crop_water_predictor
from backend.ml.marketplace.predict import marketplace_predictor
from backend.app.seed import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("krishiraksha.main")

# â”€â”€ Create tables and seed â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Base.metadata.create_all(bind=engine)
seed_database()

# â”€â”€ FastAPI App â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_TITLE,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# AUTH
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.post("/api/auth/token", response_model=Token, tags=["Auth"])
def login(req: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if not admin or not verify_password(req.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(data={"sub": admin.username, "role": admin.role})
    return Token(access_token=token, token_type="bearer",
                 user_id=admin.id, username=admin.username, role=admin.role)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SYSTEM STATUS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.get("/api/system/status", tags=["System"])
def system_status(db: Session = Depends(get_db)):
    # DB
    db_status = "CONNECTED"
    try:
        db.execute(func.now() if engine.dialect.name != "sqlite" else func.count(State.id))
    except Exception:
        db_status = "ERROR"

    # Weather
    weather_status = "CONNECTED" if imd_client.last_successful_update else "AWAITING_FIRST_SYNC"
    last_obs = db.query(WeatherObservation).order_by(WeatherObservation.retrieved_at.desc()).first()
    last_weather_update = last_obs.retrieved_at if last_obs else None

    # ML
    ml_status = "READY" if model_registry.is_model_ready() else "NOT_TRAINED"

    # Crop Water ML
    crop_water_status = "READY" if crop_water_predictor.is_ready() else "NOT_TRAINED"
    crop_water_meta = crop_water_predictor.get_metadata()

    # MLflow
    mlflow_status = "CONNECTED"
    try:
        import mlflow
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.search_experiments()
    except Exception:
        mlflow_status = "ERROR"

    # SMS
    sms_cfg = msg91_service.get_config_status()

    # DLT
    dlt_status = "CONFIGURED" if sms_cfg["dlt_registered"] else "NOT CONFIGURED"

    # Counts
    total_states = db.query(State).count()
    total_districts = db.query(District).count()
    active_farmers = db.query(Farmer).filter(Farmer.is_active == True).count()

    # Risk counts from latest assessments
    latest_risks = db.query(RiskAssessment.final_risk_level, func.count(RiskAssessment.id)).group_by(
        RiskAssessment.final_risk_level).all()
    risk_map = dict(latest_risks)

    # Warnings
    now = datetime.utcnow()
    warnings_count = db.query(OfficialWarning).filter(
        OfficialWarning.warning_color.in_(["ORANGE", "RED"]),
        OfficialWarning.valid_to >= now
    ).count()

    alerts_today = db.query(Alert).filter(
        Alert.created_at >= now.replace(hour=0, minute=0, second=0)
    ).count()

    last_pred = db.query(Prediction).order_by(Prediction.prediction_time.desc()).first()

    return {
        "weather_api": weather_status,
        "database": db_status,
        "ml_model": ml_status,
        "crop_water_ml": crop_water_status,
        "crop_water_status": crop_water_status,
        "crop_water_version": crop_water_meta.get("version", "N/A") if crop_water_meta else "N/A",
        "marketplace_ml": "READY" if marketplace_predictor.is_ready() else "NOT_TRAINED",
        "mlflow": mlflow_status,
        "sms_gateway": sms_cfg["gateway_status"],
        "dlt": dlt_status,
        "last_weather_update": last_weather_update,
        "last_prediction_update": last_pred.prediction_time if last_pred else None,
        "total_states_monitored": total_states,
        "total_districts_monitored": total_districts,
        "low_risk_count": risk_map.get("LOW", 0),
        "moderate_risk_count": risk_map.get("MODERATE", 0),
        "high_risk_count": risk_map.get("HIGH", 0),
        "very_high_risk_count": risk_map.get("VERY_HIGH", 0),
        "official_warnings_count": warnings_count,
        "active_farmers_count": active_farmers,
        "alerts_today": alerts_today,
        "sms_mode": sms_cfg["sms_mode"],
        "timestamp": datetime.utcnow()
    }

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# STATES & DISTRICTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.get("/api/states", tags=["Geography"])
def list_states(db: Session = Depends(get_db)):
    states = db.query(State).all()
    result = []
    for s in states:
        farmer_count = db.query(Farmer).filter(Farmer.state_id == s.id, Farmer.is_active == True).count()
        alert_count = db.query(Alert).filter(Alert.state_id == s.id, Alert.status == "ACTIVE").count()
        latest_risk = db.query(RiskAssessment).join(District).filter(
            District.state_id == s.id
        ).order_by(RiskAssessment.assessment_time.desc()).first()

        result.append({
            "id": s.id, "code": s.code, "name": s.name,
            "latitude": s.latitude, "longitude": s.longitude,
            "default_language": s.default_language,
            "current_risk": latest_risk.final_risk_level if latest_risk else "LOW",
            "official_warning": latest_risk.official_warning_level if latest_risk else "GREEN",
            "affected_districts_count": db.query(RiskAssessment).join(District).filter(
                District.state_id == s.id, RiskAssessment.final_risk_level.in_(["HIGH", "VERY_HIGH"])
            ).count(),
            "total_farmers": farmer_count,
            "total_alerts": alert_count,
        })
    return result

@app.get("/api/states/{state_id}/districts", tags=["Geography"])
def list_districts(state_id: int, db: Session = Depends(get_db)):
    districts = db.query(District).filter(District.state_id == state_id).all()
    result = []
    for d in districts:
        latest_risk = db.query(RiskAssessment).filter(
            RiskAssessment.district_id == d.id
        ).order_by(RiskAssessment.assessment_time.desc()).first()
        latest_obs = db.query(WeatherObservation).filter(
            WeatherObservation.district_id == d.id
        ).order_by(WeatherObservation.retrieved_at.desc()).first()
        latest_fc = db.query(WeatherForecast).filter(
            WeatherForecast.district_id == d.id
        ).order_by(WeatherForecast.retrieved_at.desc()).first()

        result.append({
            "id": d.id, "state_id": d.state_id, "code": d.code, "name": d.name,
            "latitude": d.latitude, "longitude": d.longitude,
            "current_risk": latest_risk.final_risk_level if latest_risk else "LOW",
            "official_warning": latest_risk.official_warning_level if latest_risk else "GREEN",
            "current_rainfall": latest_obs.rainfall if latest_obs else 0.0,
            "forecast_rainfall": latest_fc.expected_rainfall_24h if latest_fc else 0.0,
            "risk_score": latest_risk.risk_score if latest_risk else 0.0,
        })
    return result

@app.get("/api/districts", tags=["Geography"])
def list_all_districts(db: Session = Depends(get_db)):
    districts = db.query(District).all()
    result = []
    for d in districts:
        state = db.query(State).filter(State.id == d.state_id).first()
        latest_risk = db.query(RiskAssessment).filter(
            RiskAssessment.district_id == d.id
        ).order_by(RiskAssessment.assessment_time.desc()).first()
        latest_obs = db.query(WeatherObservation).filter(
            WeatherObservation.district_id == d.id
        ).order_by(WeatherObservation.retrieved_at.desc()).first()

        result.append({
            "id": d.id, "state_id": d.state_id,
            "state_name": state.name if state else "",
            "code": d.code, "name": d.name,
            "latitude": d.latitude, "longitude": d.longitude,
            "current_risk": latest_risk.final_risk_level if latest_risk else "LOW",
            "official_warning": latest_risk.official_warning_level if latest_risk else "GREEN",
            "current_rainfall": latest_obs.rainfall if latest_obs else 0.0,
            "risk_score": latest_risk.risk_score if latest_risk else 0.0,
        })
    return result

@app.get("/api/districts/{district_id}", tags=["Geography"])
def get_district_detail(district_id: int, db: Session = Depends(get_db)):
    d = db.query(District).filter(District.id == district_id).first()
    if not d:
        raise HTTPException(404, "District not found")
    state = db.query(State).filter(State.id == d.state_id).first()
    obs = db.query(WeatherObservation).filter(
        WeatherObservation.district_id == d.id
    ).order_by(WeatherObservation.retrieved_at.desc()).first()
    fc = db.query(WeatherForecast).filter(
        WeatherForecast.district_id == d.id
    ).order_by(WeatherForecast.retrieved_at.desc()).first()
    risk = db.query(RiskAssessment).filter(
        RiskAssessment.district_id == d.id
    ).order_by(RiskAssessment.assessment_time.desc()).first()

    # Recent 7-day accumulation
    week_ago = datetime.utcnow() - timedelta(days=7)
    acc_7d = db.query(func.sum(WeatherObservation.rainfall)).filter(
        WeatherObservation.district_id == d.id,
        WeatherObservation.retrieved_at >= week_ago
    ).scalar() or 0.0

    farmer_count = db.query(Farmer).filter(Farmer.district_id == d.id, Farmer.is_active == True).count()
    factors = json.loads(risk.contributing_factors) if risk and risk.contributing_factors else ["No assessment yet"]

    return {
        "id": d.id, "name": d.name, "state_name": state.name, "state_id": d.state_id,
        "latitude": d.latitude, "longitude": d.longitude,
        "current_rainfall": obs.rainfall if obs else 0.0,
        "forecast_rainfall_24h": fc.expected_rainfall_24h if fc else 0.0,
        "forecast_rainfall_48h": fc.expected_rainfall_48h if fc else 0.0,
        "recent_accumulated_7d": round(float(acc_7d), 1),
        "temperature": obs.temperature if obs else None,
        "humidity": obs.humidity if obs else None,
        "wind_speed": obs.wind_speed if obs else None,
        "official_warning": risk.official_warning_level if risk else "GREEN",
        "ai_risk": risk.ai_risk_level if risk else "LOW",
        "risk_score": risk.risk_score if risk else 0.0,
        "prediction_confidence": risk.confidence if risk else 0.0,
        "risk_reasons": factors,
        "data_freshness": risk.data_freshness_status if risk else "DATA_INSUFFICIENT",
        "last_updated": risk.assessment_time if risk else None,
        "active_farmers_count": farmer_count,
    }

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# WEATHER
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.post("/api/weather/refresh", tags=["Weather"])
def refresh_weather(db: Session = Depends(get_db)):
    """Fetches latest weather data for all districts and stores to DB."""
    districts = db.query(District).all()
    results = []
    for d in districts:
        state = db.query(State).filter(State.id == d.state_id).first()
        if not state:
            continue

        # Fetch observation
        obs_data = imd_client.fetch_district_rainfall(state.name, d.name, d.latitude, d.longitude)
        rainfall = float(obs_data.get("rainfall", 0.0))
        temp = obs_data.get("temperature")
        hum = obs_data.get("humidity")
        ws = obs_data.get("wind_speed")
        freshness = obs_data.get("freshness", "DATA_INSUFFICIENT")

        # Fetch warnings
        warn_data = imd_client.fetch_district_warnings(state.name, d.name, rainfall)
        w_color = warn_data.get("warning_color", "GREEN")
        w_level = warn_data.get("warning_level", "NO_WARNING")

        # Fetch forecast
        fc_data = imd_client.fetch_forecast_data(state.name, d.name, d.latitude, d.longitude)
        fc_24 = float(fc_data.get("expected_rainfall_24h", 0.0))
        fc_48 = float(fc_data.get("expected_rainfall_48h", 0.0))
        fc_color = fc_data.get("warning_color", "GREEN")

        now = datetime.utcnow()

        # Save observation
        wo = WeatherObservation(
            source=obs_data.get("source", "IMD"), state_id=state.id, district_id=d.id,
            observation_time=now, rainfall=rainfall,
            temperature=float(temp) if temp else None,
            humidity=float(hum) if hum else None,
            wind_speed=float(ws) if ws else None,
            warning_code=w_level, warning_color=w_color,
            raw_response_hash=obs_data.get("raw_hash"),
            retrieved_at=now
        )
        db.add(wo)

        # Save forecast
        wf = WeatherForecast(
            source=fc_data.get("source", "IMD"), state_id=state.id, district_id=d.id,
            forecast_time=now, expected_rainfall_24h=fc_24, expected_rainfall_48h=fc_48,
            warning_color=fc_color, retrieved_at=now
        )
        db.add(wf)

        # Save official warning
        ow = OfficialWarning(
            source=warn_data.get("source", "IMD"), state_id=state.id, district_id=d.id,
            warning_level=w_level, warning_color=w_color,
            valid_from=now, valid_to=now + timedelta(hours=48),
            description=warn_data.get("description", ""),
            retrieved_at=now
        )
        db.add(ow)

        results.append({
            "district": d.name, "state": state.name,
            "rainfall": rainfall, "forecast_24h": fc_24,
            "warning": w_color, "freshness": freshness
        })

    db.commit()
    log = SystemLog(component="WEATHER_API", level="INFO",
                    message=f"Weather refresh completed for {len(results)} districts")
    db.add(log)
    db.commit()
    return {"status": "SUCCESS", "districts_updated": len(results), "details": results}

@app.get("/api/weather/history", tags=["Weather"])
def weather_history(district_id: Optional[int] = None, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(WeatherObservation)
    if district_id:
        q = q.filter(WeatherObservation.district_id == district_id)
    obs = q.order_by(WeatherObservation.retrieved_at.desc()).limit(limit).all()
    return [{"id": o.id, "district_id": o.district_id, "source": o.source,
             "rainfall": o.rainfall, "temperature": o.temperature,
             "humidity": o.humidity, "wind_speed": o.wind_speed,
             "warning_color": o.warning_color, "retrieved_at": o.retrieved_at} for o in obs]

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# PREDICTIONS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.post("/api/predictions/run", tags=["Predictions"])
def run_predictions(db: Session = Depends(get_db)):
    """Runs ML prediction + risk assessment for every district."""
    districts = db.query(District).all()
    results = []
    for d in districts:
        state = db.query(State).filter(State.id == d.state_id).first()
        if not state:
            continue

        # Get recent observations for this district
        recent_obs = db.query(WeatherObservation).filter(
            WeatherObservation.district_id == d.id
        ).order_by(WeatherObservation.retrieved_at.desc()).limit(7).all()

        if not recent_obs:
            results.append({"district": d.name, "status": "NO_DATA"})
            continue

        latest = recent_obs[0]
        rainfall_hist = [o.rainfall for o in recent_obs]
        freshness = imd_client.get_data_freshness(latest.retrieved_at)

        # ML prediction
        pred = predict_heavy_rain_risk(
            rainfall_history=rainfall_hist,
            temperature=latest.temperature,
            humidity=latest.humidity,
            wind_speed=latest.wind_speed,
            month=latest.retrieved_at.month if latest.retrieved_at else 7,
            data_freshness=freshness
        )

        # Save prediction
        meta = model_registry.get_metadata() or {}
        p = Prediction(
            district_id=d.id,
            model_name=meta.get("model_name", "unknown"),
            model_version=meta.get("version", "unknown"),
            features_version=pred.get("features_version", "v1"),
            prediction_time=datetime.utcnow(),
            heavy_rain_prob=pred["heavy_rain_prob"],
            predicted_class=pred["predicted_class"],
            confidence=pred["confidence"],
            input_features=json.dumps(pred.get("features_used", {}))
        )
        db.add(p)

        # Get forecast & warning for risk engine
        fc = db.query(WeatherForecast).filter(
            WeatherForecast.district_id == d.id
        ).order_by(WeatherForecast.retrieved_at.desc()).first()

        week_ago = datetime.utcnow() - timedelta(days=7)
        acc_7d = db.query(func.sum(WeatherObservation.rainfall)).filter(
            WeatherObservation.district_id == d.id,
            WeatherObservation.retrieved_at >= week_ago
        ).scalar() or 0.0

        risk_result = risk_engine.calculate_risk(
            district_name=d.name, state_name=state.name,
            ml_heavy_rain_prob=pred["heavy_rain_prob"],
            ml_confidence=pred["confidence"],
            official_warning_color=latest.warning_color or "GREEN",
            current_rainfall_24h=latest.rainfall,
            forecast_rainfall_24h=fc.expected_rainfall_24h if fc else 0.0,
            forecast_rainfall_48h=fc.expected_rainfall_48h if fc else 0.0,
            recent_accumulated_7d=float(acc_7d),
            data_freshness=freshness
        )

        ra = RiskAssessment(
            district_id=d.id,
            assessment_time=datetime.utcnow(),
            ai_risk_level=risk_result["ai_risk_level"],
            official_warning_level=risk_result["official_warning_level"],
            final_risk_level=risk_result["final_risk_level"],
            risk_score=risk_result["risk_score"],
            confidence=risk_result["confidence"],
            contributing_factors=json.dumps(risk_result["contributing_factors"]),
            data_freshness_status=risk_result["data_freshness_status"]
        )
        db.add(ra)

        results.append({
            "district": d.name, "state": state.name,
            "risk": risk_result["final_risk_level"],
            "score": risk_result["risk_score"],
            "warning": risk_result["official_warning_level"]
        })

    db.commit()
    return {"status": "SUCCESS", "predictions": len(results), "details": results}

@app.get("/api/predictions/latest", tags=["Predictions"])
def latest_predictions(db: Session = Depends(get_db)):
    """Returns latest risk assessment per district."""
    districts = db.query(District).all()
    result = []
    for d in districts:
        state = db.query(State).filter(State.id == d.state_id).first()
        risk = db.query(RiskAssessment).filter(
            RiskAssessment.district_id == d.id
        ).order_by(RiskAssessment.assessment_time.desc()).first()
        if risk:
            factors = json.loads(risk.contributing_factors) if risk.contributing_factors else []
            result.append({
                "district_id": d.id, "district_name": d.name,
                "state_name": state.name if state else "",
                "ai_risk_level": risk.ai_risk_level,
                "official_warning_level": risk.official_warning_level,
                "final_risk_level": risk.final_risk_level,
                "risk_score": risk.risk_score,
                "confidence": risk.confidence,
                "contributing_factors": factors,
                "data_freshness_status": risk.data_freshness_status,
                "assessment_time": risk.assessment_time,
            })
    return result

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FARMERS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.post("/api/farmers", tags=["Farmers"])
def register_farmer(farmer: FarmerCreate, db: Session = Depends(get_db)):
    existing = db.query(Farmer).filter(Farmer.mobile_number == farmer.mobile_number).first()
    if existing:
        raise HTTPException(400, "Mobile number already registered")
    state = db.query(State).filter(State.id == farmer.state_id).first()
    district = db.query(District).filter(District.id == farmer.district_id).first()
    if not state or not district:
        raise HTTPException(400, "Invalid state or district ID")
    f = Farmer(**farmer.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    masked = f"+91******{f.mobile_number[-4:]}"
    return {"id": f.id, "full_name": f.full_name, "mobile_number_masked": masked,
            "state_name": state.name, "district_name": district.name,
            "preferred_language": f.preferred_language, "crop": f.crop, "message": "Farmer registered successfully"}

@app.get("/api/farmers", tags=["Farmers"])
def list_farmers(state_id: Optional[int] = None, district_id: Optional[int] = None,
                 db: Session = Depends(get_db)):
    q = db.query(Farmer)
    if state_id:
        q = q.filter(Farmer.state_id == state_id)
    if district_id:
        q = q.filter(Farmer.district_id == district_id)
    farmers = q.all()
    result = []
    for f in farmers:
        state = db.query(State).filter(State.id == f.state_id).first()
        dist = db.query(District).filter(District.id == f.district_id).first()
        result.append({
            "id": f.id, "full_name": f.full_name,
            "mobile_number_masked": f"+91******{f.mobile_number[-4:]}",
            "state_id": f.state_id, "state_name": state.name if state else "",
            "district_id": f.district_id, "district_name": dist.name if dist else "",
            "mandal_block": f.mandal_block, "preferred_language": f.preferred_language,
            "crop": f.crop, "crop_stage": f.crop_stage,
            "is_active": f.is_active, "created_at": f.created_at
        })
    return result

@app.get("/api/farmers/stats", tags=["Farmers"])
def farmer_stats(db: Session = Depends(get_db)):
    total = db.query(Farmer).count()
    active = db.query(Farmer).filter(Farmer.is_active == True).count()
    by_state = db.query(State.name, func.count(Farmer.id)).join(Farmer).group_by(State.name).all()
    by_lang = db.query(Farmer.preferred_language, func.count(Farmer.id)).group_by(Farmer.preferred_language).all()
    return {"total": total, "active": active,
            "by_state": {s: c for s, c in by_state},
            "by_language": {l: c for l, c in by_lang}}

@app.put("/api/farmers/{farmer_id}", tags=["Farmers"])
def update_farmer(farmer_id: int, updates: FarmerUpdate, db: Session = Depends(get_db)):
    f = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not f:
        raise HTTPException(404, "Farmer not found")
    for k, v in updates.model_dump(exclude_unset=True).items():
        setattr(f, k, v)
    db.commit()
    return {"message": "Farmer updated", "id": farmer_id}

@app.put("/api/farmers/{farmer_id}/deactivate", tags=["Farmers"])
def deactivate_farmer(farmer_id: int, db: Session = Depends(get_db)):
    f = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not f:
        raise HTTPException(404, "Farmer not found")
    f.is_active = False
    db.commit()
    return {"message": "Farmer deactivated", "id": farmer_id}

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ALERTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.get("/api/alerts", tags=["Alerts"])
def list_alerts(status_filter: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(Alert)
    if status_filter:
        q = q.filter(Alert.status == status_filter.upper())
    alerts = q.order_by(Alert.created_at.desc()).limit(limit).all()
    result = []
    for a in alerts:
        state = db.query(State).filter(State.id == a.state_id).first()
        dist = db.query(District).filter(District.id == a.district_id).first()
        sms_count = db.query(SmsMessage).filter(SmsMessage.alert_id == a.id).count()
        result.append({
            "id": a.id, "alert_fingerprint": a.alert_fingerprint,
            "state_id": a.state_id, "state_name": state.name if state else "",
            "district_id": a.district_id, "district_name": dist.name if dist else "",
            "risk_level": a.risk_level, "official_warning": a.official_warning,
            "forecast_period": a.forecast_period, "headline": a.headline,
            "description_en": a.description_en, "created_at": a.created_at,
            "status": a.status, "recipients_count": sms_count
        })
    return result

@app.post("/api/alerts/generate", tags=["Alerts"])
def generate_alert(req: SimulateAlertRequest, db: Session = Depends(get_db)):
    """
    Generate and dispatch a district-level early warning alert.
    Returns a structured result dict — never crashes the server with HTTP 500.
    """
    import traceback as _tb
    try:
        result = alert_service.evaluate_and_dispatch_alert(
            db=db, district_id=req.district_id,
            risk_level=req.risk_level, official_warning="ORANGE",
            forecast_period="Next 24-48 Hours", force_send=req.send_sms
        )
        return result
    except Exception as exc:
        logger.error(
            f"[ALERT ENDPOINT] Unhandled exception in /api/alerts/generate: "
            f"{type(exc).__name__}: {exc}\n{_tb.format_exc()}"
        )
        return {
            "status": "ERROR",
            "message": f"Alert generation failed internally: {type(exc).__name__}. Check server logs."
        }

@app.post("/api/alerts/simulate-preview", tags=["Alerts"])
def simulate_preview(req: SimulateAlertRequest, db: Session = Depends(get_db)):
    district = db.query(District).filter(District.id == req.district_id).first()
    state = db.query(State).filter(State.id == req.state_id).first()
    if not district or not state:
        raise HTTPException(400, "Invalid state/district")

    farmers = db.query(Farmer).filter(
        Farmer.district_id == req.district_id, Farmer.is_active == True
    ).all()
    lang_breakdown = {}
    for f in farmers:
        lang = language_service.resolve_language(f.preferred_language, state.name)
        lang_breakdown[lang] = lang_breakdown.get(lang, 0) + 1

    templates = {}
    for lang in lang_breakdown:
        templates[lang] = language_service.render_sms_content(lang, district.name, state.name)

    return {
        "state_name": state.name, "district_name": district.name,
        "risk_level": req.risk_level, "affected_farmers_count": len(farmers),
        "language_breakdown": lang_breakdown, "templates_preview": templates,
        "sms_mode": msg91_service.mode
    }

# ══════════════════════════════════════════════════════════════════════════
# STATE-WISE SMS BROADCAST
# ══════════════════════════════════════════════════════════════════════════

@app.get("/api/alerts/states-with-farmers", tags=["Alerts"])
def states_with_farmers(db: Session = Depends(get_db)):
    """
    Returns all states that have at least one active farmer with a valid mobile number.
    Used to populate the state-selector dropdown in the UI.
    """
    import re as _re
    states = db.query(State).all()
    result = []
    for s in states:
        total = db.query(Farmer).filter(
            Farmer.state_id == s.id, Farmer.is_active == True
        ).count()
        result.append({
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "default_language": s.default_language,
            "active_farmers": total
        })
    # Sort: states with farmers first
    result.sort(key=lambda x: -x["active_farmers"])
    return result


class StateBroadcastRequest(BaseModel):
    state_id: int
    risk_level: str = "HIGH"
    official_warning: str = "ORANGE"
    forecast_period: str = "Next 24-48 Hours"

class StateBroadcastPreviewRequest(BaseModel):
    state_id: int
    risk_level: str = "HIGH"


@app.post("/api/alerts/state-broadcast-preview", tags=["Alerts"])
def state_broadcast_preview(req: StateBroadcastPreviewRequest, db: Session = Depends(get_db)):
    """
    Preview how many eligible farmers will be targeted by a state-wide broadcast.
    Returns counts and language breakdown BEFORE sending any SMS.
    """
    import re as _re
    state = db.query(State).filter(State.id == req.state_id).first()
    if not state:
        raise HTTPException(404, f"State ID {req.state_id} not found")

    all_farmers = db.query(Farmer).filter(
        Farmer.state_id == req.state_id,
        Farmer.is_active == True
    ).all()

    total = len(all_farmers)
    eligible = 0
    skipped_no_mobile = 0
    skipped_duplicate = 0
    seen_mobiles = set()
    lang_breakdown = {}

    for f in all_farmers:
        mob = (f.mobile_number or "").strip()
        if not mob:
            skipped_no_mobile += 1
            continue
        cleaned = _re.sub(r"[\s\-\(\)]", "", mob)
        if cleaned.startswith("+91"):
            cleaned = cleaned[3:]
        elif cleaned.startswith("91") and len(cleaned) == 12:
            cleaned = cleaned[2:]
        if not (_re.match(r"^[6-9]\d{9}$", cleaned)):
            skipped_no_mobile += 1
            continue
        normalized = _re.sub(r"\D", "", mob)
        if normalized in seen_mobiles:
            skipped_duplicate += 1
            continue
        seen_mobiles.add(normalized)
        eligible += 1
        lang = language_service.resolve_language(f.preferred_language, state.name)
        lang_breakdown[lang] = lang_breakdown.get(lang, 0) + 1

    return {
        "state_id": state.id,
        "state_name": state.name,
        "risk_level": req.risk_level,
        "total_active_farmers": total,
        "eligible_farmers": eligible,
        "skipped_no_mobile": skipped_no_mobile,
        "skipped_duplicate": skipped_duplicate,
        "language_breakdown": lang_breakdown,
        "sms_mode": msg91_service.mode
    }


@app.post("/api/alerts/state-broadcast", tags=["Alerts"])
def state_broadcast(req: StateBroadcastRequest, db: Session = Depends(get_db)):
    """
    STATE-WIDE BROADCAST: Sends a rain/flood alert SMS to ALL eligible active farmers
    in the given state. Dynamically queries the farmer database — no hardcoded lists.

    Safety:
    - Validates mobile numbers
    - Deduplicates by phone number
    - Skips inactive farmers
    - Never stops on individual SMS failure
    - Returns per-farmer tracking + summary stats
    """
    import traceback as _tb
    try:
        result = alert_service.dispatch_state_broadcast(
            db=db,
            state_id=req.state_id,
            risk_level=req.risk_level,
            official_warning=req.official_warning,
            forecast_period=req.forecast_period
        )
        return result
    except Exception as exc:
        logger.error(
            f"[STATE BROADCAST ENDPOINT] Unhandled exception: "
            f"{type(exc).__name__}: {exc}\n{_tb.format_exc()}"
        )
        return {
            "status": "ERROR",
            "message": f"State broadcast failed internally: {type(exc).__name__}. Check server logs."
        }

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SMS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.post("/api/sms/test", tags=["SMS"])
def send_test_sms(req: TestSmsRequest, db: Session = Depends(get_db)):
    result = msg91_service.send_single_sms(
        mobile_number=req.mobile_number, language=req.language,
        state_name=req.state_name, district_name=req.district_name,
        period=req.period
    )
    return {
        "status": result["status"], "provider": result.get("provider", "MSG91"),
        "sms_mode": result.get("mode", "demo"),
        "message": result["message"],
        "provider_response": result.get("provider_response", {}),
        "dlt_template_id": result.get("template_id"),
        "rendered_text": result.get("rendered_text", "")
    }

@app.get("/api/sms/logs", tags=["SMS"])
def sms_logs(limit: int = 50, status_filter: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(SmsMessage)
    if status_filter:
        q = q.filter(SmsMessage.status == status_filter.upper())
    msgs = q.order_by(SmsMessage.submitted_at.desc()).limit(limit).all()
    result = []
    for m in msgs:
        farmer = db.query(Farmer).filter(Farmer.id == m.farmer_id).first()
        result.append({
            "id": m.id, "farmer_id": m.farmer_id,
            "farmer_name": farmer.full_name if farmer else "Unknown",
            "mobile_masked": m.mobile_masked, "alert_id": m.alert_id,
            "language": m.language, "template_id": m.template_id,
            "provider": m.provider, "provider_message_id": m.provider_message_id,
            "submitted_at": m.submitted_at, "delivered_at": m.delivered_at,
            "status": m.status, "failure_reason": m.failure_reason
        })
    return result

@app.get("/api/sms/config", tags=["SMS"])
def sms_config():
    return msg91_service.get_config_status()

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ML MODEL
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.get("/api/ml/metrics", tags=["ML"])
def ml_metrics(db: Session = Depends(get_db)):
    meta = model_registry.get_metadata()
    if not meta:
        return {"status": "NOT_TRAINED", "message": "No ML model has been trained yet."}
    metrics = meta.get("metrics", {})
    return {
        "model_name": meta.get("model_name"),
        "model_version": meta.get("version"),
        "algorithm": meta.get("algorithm"),
        "accuracy": metrics.get("accuracy", 0),
        "precision": metrics.get("precision", 0),
        "recall": metrics.get("recall", 0),
        "f1_score": metrics.get("f1_score", 0),
        "roc_auc": metrics.get("roc_auc", 0),
        "training_dataset_size": meta.get("training_dataset_size", 0),
        "test_dataset_size": meta.get("test_dataset_size", 0),
        "training_period": meta.get("training_period", ""),
        "data_source": meta.get("data_source", ""),
        "trained_at": meta.get("trained_at"),
        "is_active": True,
        "confusion_matrix": metrics.get("confusion_matrix", []),
        "feature_importance": metrics.get("feature_importance", {}),
        "all_candidates": meta.get("all_candidate_metrics", {}),
        "target_definition": meta.get("target_definition", ""),
        "distinction_note": meta.get("distinction_note", "")
    }

@app.post("/api/ml/train", tags=["ML"])
def trigger_training(background_tasks: BackgroundTasks):
    from backend.ml.train import train_and_evaluate_all_models
    background_tasks.add_task(train_and_evaluate_all_models)
    return {"status": "TRAINING_STARTED", "message": "ML training pipeline launched in background."}

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# LANGUAGES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.get("/api/languages", tags=["Languages"])
def supported_languages():
    return {"languages": SUPPORTED_LANGUAGES, "templates": language_service.get_all_templates_status()}

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MONITORING CYCLE (combined weather+prediction+alert in one call)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.post("/api/monitor/cycle", tags=["Monitoring"])
def run_monitoring_cycle(db: Session = Depends(get_db)):
    """Full automated monitoring cycle: fetch â†’ predict â†’ assess â†’ alert."""
    # 1. Refresh weather
    weather_result = refresh_weather(db)

    # 2. Run predictions
    pred_result = run_predictions(db)

    # 3. Auto-generate alerts for HIGH/VERY_HIGH districts
    alerts_generated = []
    districts = db.query(District).all()
    for d in districts:
        risk = db.query(RiskAssessment).filter(
            RiskAssessment.district_id == d.id
        ).order_by(RiskAssessment.assessment_time.desc()).first()
        if risk and risk.final_risk_level in ["HIGH", "VERY_HIGH"]:
            result = alert_service.evaluate_and_dispatch_alert(
                db=db, district_id=d.id,
                risk_level=risk.final_risk_level,
                official_warning=risk.official_warning_level
            )
            alerts_generated.append(result)

    return {
        "status": "CYCLE_COMPLETE",
        "weather": weather_result,
        "predictions": pred_result,
        "alerts_generated": len(alerts_generated),
        "alert_details": alerts_generated
    }

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# REPORTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.get("/api/reports/daily-risk", tags=["Reports"])
def daily_risk_report(db: Session = Depends(get_db)):
    districts = db.query(District).all()
    rows = []
    for d in districts:
        state = db.query(State).filter(State.id == d.state_id).first()
        risk = db.query(RiskAssessment).filter(
            RiskAssessment.district_id == d.id
        ).order_by(RiskAssessment.assessment_time.desc()).first()
        obs = db.query(WeatherObservation).filter(
            WeatherObservation.district_id == d.id
        ).order_by(WeatherObservation.retrieved_at.desc()).first()
        rows.append({
            "state": state.name if state else "", "district": d.name,
            "rainfall": obs.rainfall if obs else 0.0,
            "risk_level": risk.final_risk_level if risk else "LOW",
            "risk_score": risk.risk_score if risk else 0.0,
            "official_warning": risk.official_warning_level if risk else "GREEN",
            "assessment_time": str(risk.assessment_time) if risk else None
        })
    return {"report": "Daily Risk Report", "date": str(datetime.utcnow().date()), "data": rows}

@app.get("/api/reports/sms-summary", tags=["Reports"])
def sms_summary_report(db: Session = Depends(get_db)):
    total = db.query(SmsMessage).count()
    by_status = db.query(SmsMessage.status, func.count(SmsMessage.id)).group_by(SmsMessage.status).all()
    by_lang = db.query(SmsMessage.language, func.count(SmsMessage.id)).group_by(SmsMessage.language).all()
    return {"total_sms": total, "by_status": dict(by_status), "by_language": dict(by_lang)}

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SYSTEM LOGS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.get("/api/system/logs", tags=["System"])
def system_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(SystemLog).order_by(SystemLog.created_at.desc()).limit(limit).all()
    return [{"id": l.id, "component": l.component, "level": l.level,
             "message": l.message, "created_at": l.created_at} for l in logs]

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CROP WATER INTELLIGENCE (ML Extension Module)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.post("/api/crop-water/predict", tags=["Crop Water Intelligence"])
def crop_water_predict(payload: dict):
    """
    Run ML prediction for crop water requirement, water status, and stress level.
    Expects: crop, growth_stage, soil_type, soil_moisture, recent_rainfall,
    forecast_rainfall, temperature, humidity, wind_speed.
    """
    required_fields = [
        "crop", "growth_stage", "soil_type", "soil_moisture",
        "recent_rainfall", "forecast_rainfall", "temperature", "humidity", "wind_speed"
    ]
    for field in required_fields:
        if field not in payload:
            raise HTTPException(400, f"Missing required field: {field}")

    result = crop_water_predictor.predict(
        crop=payload["crop"],
        growth_stage=payload["growth_stage"],
        soil_type=payload["soil_type"],
        soil_moisture=float(payload["soil_moisture"]),
        recent_rainfall=float(payload["recent_rainfall"]),
        forecast_rainfall=float(payload["forecast_rainfall"]),
        temperature=float(payload["temperature"]),
        humidity=float(payload["humidity"]),
        wind_speed=float(payload["wind_speed"]),
    )

    if result.get("error"):
        raise HTTPException(503, result.get("message", "Model not ready"))

    return result


@app.get("/api/crop-water/model-status", tags=["Crop Water Intelligence"])
def crop_water_model_status():
    """Returns model readiness and training metadata for the crop water module."""
    metadata = crop_water_predictor.get_metadata()
    if not metadata:
        return {
            "ready": False,
            "message": "Crop Water ML models have not been trained yet."
        }
    return {
        "ready": True,
        "version": metadata.get("version", "unknown"),
        "trained_at": metadata.get("trained_at"),
        "dataset_source": metadata.get("dataset_source"),
        "training_samples": metadata.get("training_dataset_size", 0),
        "test_samples": metadata.get("test_dataset_size", 0),
        "regression": metadata.get("regression", {}),
        "classification": metadata.get("classification", {}),
        "stress_classification": metadata.get("stress_classification", {}),
        "disease_classification": metadata.get("disease_classification", {}),
        "treatment_classification": metadata.get("treatment_classification", {}),
        "recovery_classification": metadata.get("recovery_classification", {}),
        "treatment_metadata": metadata.get("treatment_metadata", {}),
        "supported_crops": metadata.get("supported_crops", []),
        "supported_stages": metadata.get("supported_stages", []),
        "supported_soils": metadata.get("supported_soils", []),
        "scientific_disclaimers": metadata.get("scientific_disclaimers", {}),
    }


@app.get("/api/crop-water/feature-importance", tags=["Crop Water Intelligence"])
def crop_water_feature_importance():
    """Returns feature importance from the champion classifier."""
    metadata = crop_water_predictor.get_metadata()
    if not metadata:
        raise HTTPException(503, "Models not trained")
    return {
        "feature_importance": metadata.get("feature_importance", {}),
        "classifier_algorithm": metadata.get("classification", {}).get("champion_algorithm", "Unknown"),
    }


@app.post("/api/crop-water/train", tags=["Crop Water Intelligence"])
def trigger_crop_water_training(background_tasks: BackgroundTasks):
    """Re-trains the crop water ML models in background."""
    from backend.ml.crop_water.train import train_and_evaluate_all
    background_tasks.add_task(train_and_evaluate_all)
    return {"status": "TRAINING_STARTED", "message": "Crop Water ML training pipeline launched in background."}


# ══════════════════════════════════════════════════════════════════════════
# MARKETPLACE — CROP LISTINGS, BUYERS, PURCHASE REQUESTS & PRICE INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════

@app.get("/api/market/listings", tags=["Marketplace"])
def list_crop_listings(
    crop: Optional[str] = None,
    state: Optional[str] = None,
    status: Optional[str] = "ACTIVE",
    db: Session = Depends(get_db)
):
    """Return all crop listings from farmers."""
    from backend.app.models.models import CropListing, PurchaseRequest as PR
    q = db.query(CropListing)
    if crop:
        q = q.filter(CropListing.crop == crop)
    if state:
        q = q.filter(CropListing.state == state)
    if status:
        q = q.filter(CropListing.status == status.upper())
    listings = q.order_by(CropListing.created_at.desc()).all()
    result = []
    for l in listings:
        farmer = db.query(Farmer).filter(Farmer.id == l.farmer_id).first()
        req_count = db.query(PR).filter(PR.listing_id == l.id).count()
        result.append({
            "id": l.id, "farmer_id": l.farmer_id,
            "farmer_name": farmer.full_name if farmer else "Unknown",
            "farmer_district": farmer.mandal_block if farmer else "",
            "crop": l.crop, "variety": l.variety,
            "quantity": l.quantity, "quantity_unit": l.quantity_unit,
            "quality": l.quality, "state": l.state, "district": l.district,
            "village": l.village, "expected_price": l.expected_price,
            "available_from": l.available_from, "harvest_date": l.harvest_date,
            "description": l.description, "status": l.status,
            "purchase_requests_count": req_count, "created_at": l.created_at,
        })
    return result


@app.post("/api/market/listings", tags=["Marketplace"])
def create_crop_listing(payload: dict, db: Session = Depends(get_db)):
    """Farmer creates a new crop listing."""
    from backend.app.models.models import CropListing
    required = ["farmer_id", "crop", "quantity", "expected_price", "state", "district", "available_from", "harvest_date"]
    for field in required:
        if field not in payload:
            raise HTTPException(400, f"Missing required field: {field}")
    farmer = db.query(Farmer).filter(Farmer.id == payload["farmer_id"]).first()
    if not farmer:
        raise HTTPException(404, "Farmer not found")
    listing = CropListing(
        farmer_id=int(payload["farmer_id"]),
        crop=str(payload["crop"]),
        variety=payload.get("variety", ""),
        quantity=float(payload["quantity"]),
        quantity_unit=payload.get("quantity_unit", "quintal"),
        quality=payload.get("quality", "Grade A"),
        state=str(payload["state"]),
        district=str(payload["district"]),
        village=payload.get("village", ""),
        expected_price=float(payload["expected_price"]),
        available_from=datetime.fromisoformat(str(payload["available_from"])),
        harvest_date=datetime.fromisoformat(str(payload["harvest_date"])),
        description=payload.get("description", ""),
        status="ACTIVE",
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return {"id": listing.id, "message": "Listing created successfully", "crop": listing.crop, "status": listing.status}


@app.put("/api/market/listings/{listing_id}/status", tags=["Marketplace"])
def update_listing_status(listing_id: int, payload: dict, db: Session = Depends(get_db)):
    """Update listing status."""
    from backend.app.models.models import CropListing
    listing = db.query(CropListing).filter(CropListing.id == listing_id).first()
    if not listing:
        raise HTTPException(404, "Listing not found")
    valid = ["ACTIVE", "SOLD", "EXPIRED", "CANCELLED"]
    new_status = str(payload.get("status", "")).upper()
    if new_status not in valid:
        raise HTTPException(400, f"Status must be one of: {valid}")
    listing.status = new_status
    db.commit()
    return {"id": listing_id, "status": new_status, "message": "Status updated"}


@app.post("/api/market/buyers", tags=["Marketplace"])
def register_buyer(payload: dict, db: Session = Depends(get_db)):
    """Register a new buyer."""
    from backend.app.models.models import Buyer
    required = ["name", "mobile_or_email", "state", "district"]
    for field in required:
        if field not in payload:
            raise HTTPException(400, f"Missing required field: {field}")
    existing = db.query(Buyer).filter(Buyer.mobile_or_email == payload["mobile_or_email"]).first()
    if existing:
        return {"id": existing.id, "message": "Buyer already registered", "name": existing.name}
    buyer = Buyer(
        name=str(payload["name"]),
        mobile_or_email=str(payload["mobile_or_email"]),
        organization=payload.get("organization", ""),
        state=str(payload["state"]),
        district=str(payload["district"]),
    )
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    return {"id": buyer.id, "name": buyer.name, "message": "Buyer registered successfully"}


@app.get("/api/market/buyers", tags=["Marketplace"])
def list_buyers(db: Session = Depends(get_db)):
    from backend.app.models.models import Buyer
    buyers = db.query(Buyer).filter(Buyer.is_active == True).all()
    return [{"id": b.id, "name": b.name, "organization": b.organization, "state": b.state, "district": b.district} for b in buyers]


@app.post("/api/market/purchase-requests", tags=["Marketplace"])
def create_purchase_request(payload: dict, db: Session = Depends(get_db)):
    """Buyer sends a purchase request for a crop listing."""
    from backend.app.models.models import CropListing, Buyer, PurchaseRequest as PR
    required = ["listing_id", "buyer_id", "requested_quantity", "offered_price"]
    for field in required:
        if field not in payload:
            raise HTTPException(400, f"Missing required field: {field}")
    listing = db.query(CropListing).filter(CropListing.id == payload["listing_id"]).first()
    if not listing or listing.status != "ACTIVE":
        raise HTTPException(404, "Listing not found or not active")
    buyer = db.query(Buyer).filter(Buyer.id == payload["buyer_id"]).first()
    if not buyer:
        raise HTTPException(404, "Buyer not found")
    pr = PR(
        listing_id=int(payload["listing_id"]),
        buyer_id=int(payload["buyer_id"]),
        requested_quantity=float(payload["requested_quantity"]),
        offered_price=float(payload["offered_price"]),
        message=payload.get("message", ""),
        status="REQUESTED",
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return {"id": pr.id, "message": "Purchase request submitted", "status": pr.status}


@app.get("/api/market/purchase-requests", tags=["Marketplace"])
def list_purchase_requests(
    listing_id: Optional[int] = None,
    buyer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    from backend.app.models.models import CropListing, Buyer, PurchaseRequest as PR
    q = db.query(PR)
    if listing_id:
        q = q.filter(PR.listing_id == listing_id)
    if buyer_id:
        q = q.filter(PR.buyer_id == buyer_id)
    reqs = q.order_by(PR.created_at.desc()).all()
    result = []
    for r in reqs:
        listing = db.query(CropListing).filter(CropListing.id == r.listing_id).first()
        buyer = db.query(Buyer).filter(Buyer.id == r.buyer_id).first()
        farmer = db.query(Farmer).filter(Farmer.id == listing.farmer_id).first() if listing else None
        result.append({
            "id": r.id, "listing_id": r.listing_id,
            "crop": listing.crop if listing else "",
            "farmer_name": farmer.full_name if farmer else "Unknown",
            "buyer_id": r.buyer_id, "buyer_name": buyer.name if buyer else "Unknown",
            "requested_quantity": r.requested_quantity, "offered_price": r.offered_price,
            "message": r.message, "status": r.status, "created_at": r.created_at,
        })
    return result


@app.put("/api/market/purchase-requests/{request_id}/status", tags=["Marketplace"])
def update_purchase_request_status(request_id: int, payload: dict, db: Session = Depends(get_db)):
    from backend.app.models.models import PurchaseRequest as PR
    pr = db.query(PR).filter(PR.id == request_id).first()
    if not pr:
        raise HTTPException(404, "Purchase request not found")
    valid = ["REQUESTED", "ACCEPTED", "REJECTED", "NEGOTIATING", "CONFIRMED", "COMPLETED", "CANCELLED"]
    new_status = str(payload.get("status", "")).upper()
    if new_status not in valid:
        raise HTTPException(400, f"Status must be one of: {valid}")
    pr.status = new_status
    db.commit()
    return {"id": request_id, "status": new_status, "message": "Request status updated"}


@app.get("/api/market/model-status", tags=["Marketplace"])
def market_model_status():
    """Returns readiness and metadata of the price forecasting model."""
    from backend.ml.marketplace.predict import marketplace_predictor
    metadata = marketplace_predictor.get_metadata()
    if not metadata:
        return {"ready": False, "message": "Price forecast model not trained. Call /api/market/train"}
    return {
        "ready": True,
        "version": metadata.get("version"),
        "trained_at": metadata.get("trained_at"),
        "champion_algorithm": metadata.get("champion_algorithm"),
        "champion_metrics": metadata.get("champion_metrics"),
        "all_candidate_metrics": metadata.get("all_candidate_metrics"),
        "training_dataset_size": metadata.get("training_dataset_size"),
        "test_dataset_size": metadata.get("test_dataset_size"),
        "data_source": metadata.get("data_source"),
        "supported_crops": metadata.get("supported_crops", []),
        "supported_markets": metadata.get("supported_markets", []),
        "price_range": metadata.get("price_range", {}),
        "scientific_note": metadata.get("scientific_note"),
    }


@app.post("/api/market/train", tags=["Marketplace"])
def trigger_market_training(background_tasks: BackgroundTasks):
    """Re-trains the crop price forecast ML model in background."""
    from backend.ml.marketplace.train import train_price_forecast_model
    background_tasks.add_task(train_price_forecast_model)
    return {"status": "TRAINING_STARTED", "message": "Crop price forecast ML training launched in background."}


@app.get("/api/market/price-forecast", tags=["Marketplace"])
def price_forecast(
    crop: str = Query(..., description="Crop name e.g. Paddy, Wheat"),
    market: str = Query(..., description="Market name e.g. Guntur, Warangal"),
    state: str = Query(default="Andhra Pradesh"),
    forecast_days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    """
    ML-based crop price forecast. Returns 7/14/30-day predictions + selling recommendation.
    DISCLAIMER: ML estimates only, not guaranteed market outcomes.
    """
    from backend.ml.marketplace.predict import marketplace_predictor
    result = marketplace_predictor.predict_price_forecast(crop=crop, market=market, state=state, forecast_days=forecast_days)
    if result.get("error"):
        raise HTTPException(503, result.get("message", "Prediction failed"))
    return result


@app.get("/api/market/overview", tags=["Marketplace"])
def market_overview(db: Session = Depends(get_db)):
    """Returns current price overview and 7-day trend for all supported crops."""
    from backend.ml.marketplace.predict import marketplace_predictor
    result = marketplace_predictor.get_market_overview()
    if result.get("error"):
        raise HTTPException(503, result.get("message", "Overview failed"))
    return result


@app.get("/api/market/supported-options", tags=["Marketplace"])
def market_supported_options():
    """Returns list of supported crops and markets."""
    from backend.ml.marketplace.predict import marketplace_predictor
    opts = marketplace_predictor.get_supported_options()
    if not opts:
        return {"crops": [], "markets": [], "note": "Model not trained yet"}
    return opts



# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FRONTEND SPA SERVING
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
from fastapi.responses import FileResponse

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


