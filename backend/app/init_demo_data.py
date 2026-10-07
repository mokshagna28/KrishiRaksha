"""
Initialize demo farmers and baseline weather/prediction data for a rich initial dashboard experience.
"""

from backend.app.database import SessionLocal, engine, Base
from backend.app.models.models import Farmer, District, State, WeatherObservation, WeatherForecast, RiskAssessment, Alert
from backend.app.seed import seed_database
from backend.app.services.weather.imd_client import imd_client
from backend.app.services.risk_engine import risk_engine
from backend.ml.predict import predict_heavy_rain_risk
import json
from datetime import datetime, timedelta

def init_demo():
    print("Initializing database...")
    seed_database()
    db = SessionLocal()
    try:
        # Check if farmers exist
        count = db.query(Farmer).count()
        if count == 0:
            print("Seeding initial farmers...")
            ap = db.query(State).filter(State.code == "AP").first()
            gnt = db.query(District).filter(District.code == "GNT").first()
            kri = db.query(District).filter(District.code == "KRI").first()
            
            kl = db.query(State).filter(State.code == "KL").first()
            wyd = db.query(District).filter(District.code == "WYD").first()

            mh = db.query(State).filter(State.code == "MH").first()
            klp = db.query(District).filter(District.code == "KLP").first()

            demo_farmers = [
                Farmer(full_name="K. Venkateswarlu", mobile_number="9876543210", state_id=ap.id, district_id=gnt.id, mandal_block="Tenali", preferred_language="Telugu", crop="Paddy", crop_stage="Flowering"),
                Farmer(full_name="S. Nageswara Rao", mobile_number="9876543211", state_id=ap.id, district_id=kri.id, mandal_block="Gudivada", preferred_language="Telugu", crop="Cotton", crop_stage="Vegetative"),
                Farmer(full_name="Mathew Thomas", mobile_number="9876543212", state_id=kl.id, district_id=wyd.id, mandal_block="Mananthavady", preferred_language="Malayalam", crop="Paddy", crop_stage="Sowing"),
                Farmer(full_name="Santosh Patil", mobile_number="9876543213", state_id=mh.id, district_id=klp.id, mandal_block="Shirol", preferred_language="Marathi", crop="Sugarcane", crop_stage="Vegetative"),
                Farmer(full_name="Rameshwar Sharma", mobile_number="9876543214", state_id=ap.id, district_id=gnt.id, mandal_block="Mangalagiri", preferred_language="Hindi", crop="Chilli", crop_stage="Harvesting"),
            ]
            for f in demo_farmers:
                db.add(f)
            db.commit()
            print(f"Seeded {len(demo_farmers)} demo farmers.")

        # Refresh weather and predictions
        print("Running initial weather & ML inference cycle...")
        districts = db.query(District).all()
        now = datetime.utcnow()
        for d in districts:
            state = db.query(State).filter(State.id == d.state_id).first()
            # Fetch or generate realistic telemetry
            obs = imd_client.fetch_district_rainfall(state.name, d.name, d.latitude, d.longitude)
            rainfall = float(obs.get("rainfall", 0.0))

            wo = WeatherObservation(
                source="IMD", state_id=state.id, district_id=d.id,
                observation_time=now, rainfall=rainfall,
                temperature=obs.get("temperature", 28.5),
                humidity=obs.get("humidity", 78.0),
                wind_speed=obs.get("wind_speed", 14.2),
                warning_code="NO_WARNING", warning_color="GREEN",
                retrieved_at=now
            )
            db.add(wo)

            fc = WeatherForecast(
                source="IMD", state_id=state.id, district_id=d.id,
                forecast_time=now, expected_rainfall_24h=rainfall * 1.2,
                expected_rainfall_48h=rainfall * 1.5,
                warning_color="GREEN", retrieved_at=now
            )
            db.add(fc)

            # Predict
            pred = predict_heavy_rain_risk(
                rainfall_history=[rainfall] * 7,
                temperature=28.5, humidity=78.0, wind_speed=14.0,
                month=7, data_freshness="FRESH"
            )

            risk_res = risk_engine.calculate_risk(
                district_name=d.name, state_name=state.name,
                ml_heavy_rain_prob=pred["heavy_rain_prob"],
                ml_confidence=pred["confidence"],
                official_warning_color="GREEN",
                current_rainfall_24h=rainfall,
                forecast_rainfall_24h=rainfall * 1.2,
                forecast_rainfall_48h=rainfall * 1.5,
                recent_accumulated_7d=rainfall * 7,
                data_freshness="FRESH"
            )

            ra = RiskAssessment(
                district_id=d.id, assessment_time=now,
                ai_risk_level=risk_res["ai_risk_level"],
                official_warning_level="GREEN",
                final_risk_level=risk_res["final_risk_level"],
                risk_score=risk_res["risk_score"],
                confidence=risk_res["confidence"],
                contributing_factors=json.dumps(risk_res["contributing_factors"]),
                data_freshness_status="FRESH"
            )
            db.add(ra)

        db.commit()
        print("Initial demo initialization complete!")
    finally:
        db.close()

if __name__ == "__main__":
    init_demo()
