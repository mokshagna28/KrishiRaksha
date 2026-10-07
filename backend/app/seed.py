"""
KRISHIRAKSHA AI - Database Seeder
Seeds states, districts, admin user, and SMS templates.
"""

import logging
from backend.app.database import SessionLocal, engine, Base
from backend.app.models.models import (
    State, District, AdminUser, SmsTemplate, ModelVersion
)
from backend.app.core.security import get_password_hash
from backend.app.config import settings
from backend.app.services.language_service import DLT_TEMPLATES

logger = logging.getLogger("krishiraksha.seed")

INDIA_STATES_DISTRICTS = [
    {"code": "AP", "name": "Andhra Pradesh", "lat": 15.9129, "lon": 79.7400, "lang": "Telugu", "districts": [
        {"code": "GNT", "name": "Guntur", "lat": 16.3067, "lon": 80.4365},
        {"code": "KRI", "name": "Krishna", "lat": 16.1875, "lon": 81.1389},
        {"code": "VSP", "name": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185},
        {"code": "EGD", "name": "East Godavari", "lat": 17.0005, "lon": 81.8040},
    ]},
    {"code": "TS", "name": "Telangana", "lat": 18.1124, "lon": 79.0193, "lang": "Telugu", "districts": [
        {"code": "HYD", "name": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
        {"code": "KHM", "name": "Khammam", "lat": 17.2473, "lon": 80.1514},
    ]},
    {"code": "KL", "name": "Kerala", "lat": 10.8505, "lon": 76.2711, "lang": "Malayalam", "districts": [
        {"code": "WYD", "name": "Wayanad", "lat": 11.6854, "lon": 76.1320},
        {"code": "IDK", "name": "Idukki", "lat": 9.8494, "lon": 76.9806},
        {"code": "EKM", "name": "Ernakulam", "lat": 9.9816, "lon": 76.2999},
    ]},
    {"code": "MH", "name": "Maharashtra", "lat": 19.7515, "lon": 75.7139, "lang": "Marathi", "districts": [
        {"code": "KLP", "name": "Kolhapur", "lat": 16.7050, "lon": 74.2433},
        {"code": "RTG", "name": "Ratnagiri", "lat": 16.9902, "lon": 73.3120},
        {"code": "PNE", "name": "Pune", "lat": 18.5204, "lon": 73.8567},
    ]},
    {"code": "KA", "name": "Karnataka", "lat": 15.3173, "lon": 75.7139, "lang": "Kannada", "districts": [
        {"code": "UDP", "name": "Udupi", "lat": 13.3409, "lon": 74.7421},
        {"code": "DKN", "name": "Dakshina Kannada", "lat": 12.8703, "lon": 74.8806},
        {"code": "KDG", "name": "Kodagu", "lat": 12.3375, "lon": 75.8069},
    ]},
    {"code": "AS", "name": "Assam", "lat": 26.2006, "lon": 92.9376, "lang": "English", "districts": [
        {"code": "KMR", "name": "Kamrup", "lat": 26.1833, "lon": 91.5667},
        {"code": "DHM", "name": "Dhemaji", "lat": 27.4833, "lon": 94.5833},
    ]},
    {"code": "BR", "name": "Bihar", "lat": 25.0961, "lon": 85.3131, "lang": "Hindi", "districts": [
        {"code": "PAT", "name": "Patna", "lat": 25.5941, "lon": 85.1376},
        {"code": "DBH", "name": "Darbhanga", "lat": 26.1542, "lon": 85.8918},
    ]},
    {"code": "OD", "name": "Odisha", "lat": 20.9517, "lon": 85.0985, "lang": "Odia", "districts": [
        {"code": "PUR", "name": "Puri", "lat": 19.8135, "lon": 85.8312},
        {"code": "CTK", "name": "Cuttack", "lat": 20.4625, "lon": 85.8830},
    ]},
    {"code": "TN", "name": "Tamil Nadu", "lat": 11.1271, "lon": 78.6569, "lang": "Tamil", "districts": [
        {"code": "TJR", "name": "Thanjavur", "lat": 10.7870, "lon": 79.1378},
        {"code": "CDL", "name": "Cuddalore", "lat": 11.7480, "lon": 79.7714},
    ]},
    {"code": "GJ", "name": "Gujarat", "lat": 22.2587, "lon": 71.1924, "lang": "Gujarati", "districts": [
        {"code": "SRT", "name": "Surat", "lat": 21.1702, "lon": 72.8311},
    ]},
    {"code": "PB", "name": "Punjab", "lat": 31.1471, "lon": 75.3412, "lang": "Punjabi", "districts": [
        {"code": "LDH", "name": "Ludhiana", "lat": 30.9010, "lon": 75.8573},
    ]},
]

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed admin
        existing_admin = db.query(AdminUser).filter(AdminUser.username == settings.ADMIN_DEFAULT_USERNAME).first()
        if not existing_admin:
            admin = AdminUser(
                username=settings.ADMIN_DEFAULT_USERNAME,
                email=settings.ADMIN_DEFAULT_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_DEFAULT_PASSWORD),
                is_active=True,
                role="ADMIN"
            )
            db.add(admin)
            logger.info("Default admin user seeded.")

        # Seed states and districts
        for st in INDIA_STATES_DISTRICTS:
            existing = db.query(State).filter(State.code == st["code"]).first()
            if not existing:
                state_obj = State(
                    code=st["code"], name=st["name"],
                    latitude=st["lat"], longitude=st["lon"],
                    default_language=st["lang"]
                )
                db.add(state_obj)
                db.flush()
                for dist in st["districts"]:
                    d_obj = District(
                        state_id=state_obj.id, code=dist["code"],
                        name=dist["name"], latitude=dist["lat"], longitude=dist["lon"]
                    )
                    db.add(d_obj)

        # Seed SMS templates
        for lang, info in DLT_TEMPLATES.items():
            existing_t = db.query(SmsTemplate).filter(SmsTemplate.language == lang).first()
            if not existing_t:
                t = SmsTemplate(
                    language=lang,
                    template_name=info["name"],
                    dlt_template_id=None,
                    content_pattern=info["pattern"],
                    is_active=True
                )
                db.add(t)

        db.commit()
        logger.info("Database seeding complete.")
    except Exception as e:
        db.rollback()
        logger.error(f"Seeding error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_database()
