"""
System Integration Test Suite for KrishiRaksha AI
Tests all API endpoints, database interactions, SMS dispatch, ML models, and Crop Water & Recovery pipeline.
"""

import os
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["database"] == "CONNECTED"
    assert data["crop_water_status"] == "READY"


def test_system_status_api():
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["total_states_monitored"] > 0
    assert data["total_districts_monitored"] > 0
    assert "active_farmers_count" in data
    assert "official_warnings_count" in data


def test_states_api():
    response = client.get("/api/states")
    assert response.status_code == 200
    states = response.json()
    assert len(states) >= 3
    state_names = [s["name"] for s in states]
    assert "Andhra Pradesh" in state_names


def test_districts_api():
    response = client.get("/api/districts")
    assert response.status_code == 200
    districts = response.json()
    assert len(districts) >= 10


def test_state_districts_api():
    response = client.get("/api/states/1/districts")
    assert response.status_code == 200
    districts = response.json()
    assert len(districts) > 0


def test_farmers_api():
    response = client.get("/api/farmers")
    assert response.status_code == 200
    farmers = response.json()
    assert len(farmers) >= 5


def test_alerts_api():
    response = client.get("/api/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)


def test_sms_logs_api():
    response = client.get("/api/sms/logs")
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)


def test_sms_config_api():
    response = client.get("/api/sms/config")
    assert response.status_code == 200
    cfg = response.json()
    assert "sms_mode" in cfg


def test_weather_refresh():
    response = client.post("/api/weather/refresh")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data or "observations_updated" in data


def test_monitor_cycle():
    response = client.post("/api/monitor/cycle")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CYCLE_COMPLETE"


def test_ml_metrics_api():
    response = client.get("/api/ml/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "GradientBoosting"
    assert data["f1_score"] > 0.95


# ══════════════════════════════════════════════════════════════════════════
# CROP WATER & EXCESS-WATER RECOVERY INTELLIGENCE MODULE TESTS
# ══════════════════════════════════════════════════════════════════════════
def test_crop_water_model_status():
    """Verify all 5 ML models in crop water pipeline are trained and ready."""
    response = client.get("/api/crop-water/model-status")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert data["version"] == "2.0.0"
    assert len(data["supported_crops"]) == 7
    assert len(data["supported_stages"]) == 4
    assert len(data["supported_soils"]) == 4
    assert data["regression"]["champion_algorithm"] == "GradientBoostingRegressor"
    assert data["regression"]["metrics"]["r2_score"] > 0.95
    assert "disease_classification" in data
    assert "treatment_classification" in data
    assert "recovery_classification" in data


def test_crop_water_predict_excess():
    """Excess rainfall scenario should predict WATERLOGGING RISK, disease, treatment, and recovery."""
    response = client.post("/api/crop-water/predict", json={
        "crop": "Rice",
        "growth_stage": "Flowering",
        "soil_type": "Clay",
        "soil_moisture": 90,
        "recent_rainfall": 180,
        "forecast_rainfall": 100,
        "temperature": 27,
        "humidity": 95,
        "wind_speed": 15,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["error"] is False
    assert "EXCESS" in data["water_status"]
    assert data["crop_stress_level"] in ["SEVERE", "HIGH"]
    assert data["crop_disease_stress"] != ""
    assert data["recommended_treatment"] != ""
    assert "treatment_name" in data["treatment_details"]
    assert "active_ingredient" in data["treatment_details"]
    assert "application_info" in data["treatment_details"]
    assert data["expected_recovery"] != ""
    assert data["confidence"] > 80
    assert "reason" in data and len(data["reason"]) > 20
    assert data["advisory"]["severity"] == "CRITICAL"


def test_crop_water_predict_optimal():
    """Moderate conditions should predict OPTIMAL WATER and Healthy condition."""
    response = client.post("/api/crop-water/predict", json={
        "crop": "Wheat",
        "growth_stage": "Vegetative",
        "soil_type": "Loam",
        "soil_moisture": 40,
        "recent_rainfall": 15,
        "forecast_rainfall": 10,
        "temperature": 25,
        "humidity": 55,
        "wind_speed": 6,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["error"] is False
    assert data["water_status"] == "OPTIMAL WATER"
    assert data["crop_stress_level"] == "LOW"
    assert "Healthy" in data["crop_disease_stress"]
    assert "No Chemical Treatment" in data["recommended_treatment"]
    assert "Full Recovery" in data["expected_recovery"]


def test_crop_water_predict_low():
    """Dry conditions should predict LOW WATER / WATER STRESS."""
    response = client.post("/api/crop-water/predict", json={
        "crop": "Maize",
        "growth_stage": "Flowering",
        "soil_type": "Sandy",
        "soil_moisture": 10,
        "recent_rainfall": 0,
        "forecast_rainfall": 0,
        "temperature": 42,
        "humidity": 20,
        "wind_speed": 25,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["error"] is False
    assert "LOW" in data["water_status"] or "STRESS" in data["water_status"]
    assert "Wilting" in data["crop_disease_stress"] or "Closure" in data["crop_disease_stress"]
    assert data["recommended_treatment"] != ""


def test_crop_water_feature_importance():
    """Feature importance endpoint returns valid importance map."""
    response = client.get("/api/crop-water/feature-importance")
    assert response.status_code == 200
    data = response.json()
    fi = data["feature_importance"]
    assert len(fi) >= 5
    total = sum(fi.values())
    assert abs(total - 1.0) < 0.01
