# KRISHIRAKSHA AI (కృషీరక్ష / कृषिरक्षा)

**AI-Based Heavy Rainfall & Flood Risk Early Warning System for Indian Farmers**  
**Student Roll Number:** 231FA04291  
**Degree:** B.Tech Final Year CSE Project

---

## 🌟 Overview

KRISHIRAKSHA AI is a production-grade, genuine early-warning system designed for Indian agriculture. It automatically monitors atmospheric conditions and telemetry across 25 agricultural districts in 11 Indian states, feeds antecedent precipitation and atmospheric moisture features into an optimized **Gradient Boosting Classifier (F1-Score: 0.9933, Precision: 0.9946, Recall: 0.9920)**, combines predictions with IMD color-coded official warnings and 7-day soil saturation levels via a multi-factor **Risk Engine**, and automatically dispatches localized, DLT-compliant SMS notifications across **11 Indian languages** via **MSG91**.

---

## 📐 System Architecture

```
                       ┌────────────────────────────────────────┐
                       │     India Meteorological Dept (IMD)    │
                       │          & Open-Meteo Telemetry        │
                       └───────────────────┬────────────────────┘
                                           │
                                           ▼
┌───────────────────────┐       ┌───────────────────────┐       ┌────────────────────────┐
│   Historical 27k+     │       │ Telemetry Ingestion   │       │ Registered Farmers     │
│   Rainfall Records    │──────▶│ & Feature Pipeline    │       │ (11 Indian Languages,  │
│   (Tracked with DVC)  │       │ (7D Saturation, Dew)  │       │ Masked DPDP compliant) │
└───────────────────────┘       └──────────┬────────────┘       └───────────┬────────────┘
                                           │                                │
                                           ▼                                │
                                ┌───────────────────────┐                   │
                                │ ML Champion Model     │                   │
                                │ (GradientBoosting)    │                   │
                                │ F1-Score: 0.9933      │                   │
                                └──────────┬────────────┘                   │
                                           │                                │
                                           ▼                                │
                                ┌───────────────────────┐                   │
                                │ Multi-Factor          │                   │
                                │ Risk Engine           │                   │
                                └──────────┬────────────┘                   │
                                           │ (HIGH / VERY HIGH)             │
                                           ▼                                │
                                ┌───────────────────────┐                   │
                                │ Early Warning Service │◀──────────────────┘
                                │ & Deduplication Engine│
                                └──────────┬────────────┘
                                           │
                                           ▼
                                ┌───────────────────────┐
                                │ MSG91 Gateway         │
                                │ 11 DLT Language Tmpls │
                                └───────────────────────┘
```

---

## 🚀 Key Features

1. **Genuinely Working Telemetry & Ingestion:**
   - Real-time weather observation & 48h forecast retrieval with automatic hashing and freshness verification (`DATA_INSUFFICIENT`, `STALE`, `FRESH`).
   - Fault-tolerant fallback between primary IMD APIs and Open-Meteo.
2. **Machine Learning & MLOps Pipeline:**
   - Benchmarked 4 candidate algorithms: Logistic Regression, Random Forest, Gradient Boosting, XGBoost.
   - Selected **Gradient Boosting Classifier** as champion with 99.33% F1-score and 0.9999 ROC-AUC.
   - Experiments logged to MLflow; dataset tracked via DVC.
3. **Multi-Factor Risk Engine:**
   - Explicit distinction between atmospheric heavy rain probability and soil inundation / flooding risk.
   - Synthesizes ML inference, official IMD district warnings, and 7-day cumulative precipitation to eliminate false alarms.
4. **TRAI / DLT-Compliant SMS Delivery Hub:**
   - 11 approved templates across: Telugu, Hindi, Tamil, Kannada, Malayalam, Marathi, Bengali, Odia, Gujarati, Punjabi, English.
   - Clean Live/Demo mode switching with real delivery state guarantees (never flags "DELIVERED" prematurely).
   - Strict DPDP Act privacy enforcement with automated mobile number masking (`+91******3210`).
5. **Modern Reactive Single-Page Application (SPA):**
   - High-contrast responsive dark interface with glassmorphism and real-time status badges.
   - Live district matrix search and filtering.
   - Detailed modal for atmospheric sensor data and soil saturation indicators.
   - Multilingual SMS alert previewer and dispatch terminal.
   - Model benchmark visualization and feature importance rankings.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.14, FastAPI, SQLAlchemy, SQLite/PostgreSQL, Pydantic v2.
- **Machine Learning:** Scikit-learn, XGBoost, MLflow, DVC, Pandas, NumPy.
- **SMS Gateway:** MSG91 REST API with DLT schema validation and simulation fallback.
- **Frontend:** React 18, TypeScript, Vite 5, Lucide Icons, Custom CSS Design System.
- **Testing:** Pytest, HTTPX, FastAPI TestClient.

---

## ⚡ Running the Application

### 1. Launch the Application Server
Run the provided launcher script:
```powershell
.\run.bat
```
Or run directly via python:
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 2. Access the Application
Open your browser and navigate to:
- **Full Web Application & Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Specifications:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 3. Run Test Suite
To verify the test suite:
```powershell
python -m pytest backend/tests/test_system.py -v
```

---

## 🧪 Core API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/system/status` | GET | Real-time health of weather API, DB, ML model, and SMS gateway |
| `/api/districts` | GET | Comprehensive list of monitored districts with current risk scores |
| `/api/districts/{id}` | GET | Telemetry deep-dive, 7-day accumulation, and AI reasoning factors |
| `/api/weather/refresh` | POST | Triggers live weather sync across all monitored districts |
| `/api/predictions/run` | POST | Executes Champion ML inference for all districts |
| `/api/monitor/cycle` | POST | Automated end-to-end loop: Ingest ➔ Predict ➔ Assess ➔ Alert |
| `/api/farmers` | GET/POST | Farmer registry with DPDP mobile masking and 11 language support |
| `/api/alerts/generate` | POST | Dispatches early warning alert to farmers in target district |
| `/api/alerts/simulate-preview` | POST | Multilingual preview of exact rendered DLT templates |
| `/api/sms/test` | POST | Interactive SMS delivery testing terminal |
| `/api/sms/logs` | GET | Complete audit trail of submitted SMS messages |
| `/api/ml/metrics` | GET | Champion model metrics, comparison table, and feature importances |
