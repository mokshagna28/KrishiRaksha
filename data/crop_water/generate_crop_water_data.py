"""
FAO-56 & ICAR Empirical Benchmark Generator for Crop Water Requirement,
Excess-Water Stress Identification, Treatment Prediction & Recovery Modeling.

Produces realistic agricultural data adhering to FAO-56 Penman-Monteith ETc standards
and ICAR Plant Pathology guidelines for waterlogging, moisture-induced diseases,
pesticide/treatment selection, and post-treatment recovery outcomes.
"""

import numpy as np
import pandas as pd
import os

np.random.seed(42)

CROPS = ["Rice", "Cotton", "Maize", "Wheat", "Sugarcane", "Pulses", "Tomato"]
STAGES = ["Sowing", "Vegetative", "Flowering", "Harvesting"]
SOILS = ["Clay", "Loam", "Sandy", "Black Cotton Soil"]

KC_TABLE = {
    "Rice": {"Sowing": 1.05, "Vegetative": 1.15, "Flowering": 1.25, "Harvesting": 0.95},
    "Cotton": {"Sowing": 0.35, "Vegetative": 0.75, "Flowering": 1.20, "Harvesting": 0.65},
    "Maize": {"Sowing": 0.40, "Vegetative": 0.80, "Flowering": 1.15, "Harvesting": 0.70},
    "Wheat": {"Sowing": 0.35, "Vegetative": 0.75, "Flowering": 1.15, "Harvesting": 0.45},
    "Sugarcane": {"Sowing": 0.45, "Vegetative": 0.85, "Flowering": 1.25, "Harvesting": 0.75},
    "Pulses": {"Sowing": 0.40, "Vegetative": 0.70, "Flowering": 1.10, "Harvesting": 0.55},
    "Tomato": {"Sowing": 0.45, "Vegetative": 0.75, "Flowering": 1.15, "Harvesting": 0.80},
}

SOIL_FACTOR = {
    "Clay": 1.2,
    "Loam": 1.0,
    "Sandy": 0.75,
    "Black Cotton Soil": 1.3,
}

# Real ICAR/FAO Agrochemical & Agronomic Treatment Dictionary
TREATMENT_LOOKUP = {
    "Healthy (No Stress)": {
        "treatment": "No Chemical Treatment Needed (Maintain Normal Irrigation)",
        "category": "Standard Care",
        "active_ingredient": "None",
        "application_info": "Continue balanced crop monitoring and standard field management."
    },
    "Stomatal Closure & Wilting": {
        "treatment": "Supplemental Precision Irrigation + Anti-transpirant Spray",
        "category": "Irrigation & Moisture Retention",
        "active_ingredient": "Potassium Nitrate (1%) + Kaolin Spray",
        "application_info": "Apply 30-50 mm irrigation during early morning hours; spray 1% KNO3 to reduce wilting."
    },
    "Soil Aeration Stress (Mild Hypoxia)": {
        "treatment": "Surface Field Drainage + Soil Aeration Ridge Formation",
        "category": "Cultural & Agronomic Drainage",
        "active_ingredient": "None (Cultural Control)",
        "application_info": "Open periphery field furrows to drain standing surface water within 24 hours."
    },
    "Waterlogging & Oxygen Depletion (Hypoxia)": {
        "treatment": "Field Trench Drainage + Potassium Nitrate Foliar Spray (1%)",
        "category": "Drainage & Nutrient Rescue",
        "active_ingredient": "Potassium Nitrate (13-0-45)",
        "application_info": "Excavate 30cm deep drainage ditches; apply 1% KNO3 foliar spray to boost root respiration."
    },
    "Pythium & Phytophthora Root Rot": {
        "treatment": "Carbendazim 50% WP + Metalaxyl-Mancozeb Drenching",
        "category": "Fungicide (Systemic)",
        "active_ingredient": "Metalaxyl 8% + Mancozeb 64% WP",
        "application_info": "Drench root zone with 2 g/L solution of Metalaxyl + Mancozeb; ensure field drainage."
    },
    "Fungal Sheath & Leaf Blight": {
        "treatment": "Copper Oxychloride 50% WP + Hexaconazole Spray",
        "category": "Fungicide (Broad Spectrum)",
        "active_ingredient": "Copper Oxychloride 50% WP",
        "application_info": "Foliar spray at 2.5 g/L water; repeat after 7-10 days if high atmospheric humidity persists."
    },
    "Damping Off Fungal Infection": {
        "treatment": "Trichoderma Viride Bio-Fungicide Soil Application",
        "category": "Biological Fungicide",
        "active_ingredient": "Trichoderma Viride (1x10^8 CFU/g)",
        "application_info": "Apply 5 kg/ha bio-agent mixed with 100 kg FYM near root zones to suppress damping-off pathogen."
    },
    "Nitrogen & Nutrient Leaching Stress": {
        "treatment": "Drainage Channel Clearing + Foliar Urea (1-2%) Spray",
        "category": "Nutrient Rescue & Drainage",
        "active_ingredient": "Urea (46% N) Foliar Grade",
        "application_info": "Spray 1.5% Urea solution (15 g/L water) on foliage after draining excess water to correct nitrogen chlorosis."
    }
}

N_SAMPLES = 4000

records = []
for i in range(N_SAMPLES):
    crop = np.random.choice(CROPS)
    stage = np.random.choice(STAGES)
    soil = np.random.choice(SOILS)
    
    # 4 Scenarios: deficit, optimal, high, excess
    scenario = np.random.choice(["deficit", "optimal", "high", "excess"], p=[0.25, 0.30, 0.25, 0.20])
    
    if scenario == "deficit":
        temp = np.round(np.random.uniform(28.0, 42.0), 1)
        humidity = np.round(np.random.uniform(25.0, 50.0), 1)
        wind = np.round(np.random.uniform(8.0, 25.0), 1)
        recent_rain = np.round(np.random.uniform(0.0, 8.0), 1)
        forecast_rain = np.round(np.random.uniform(0.0, 6.0), 1)
        soil_moisture = np.round(np.random.uniform(15.0, 32.0), 1)
    elif scenario == "optimal":
        temp = np.round(np.random.uniform(22.0, 32.0), 1)
        humidity = np.round(np.random.uniform(50.0, 72.0), 1)
        wind = np.round(np.random.uniform(5.0, 18.0), 1)
        recent_rain = np.round(np.random.uniform(8.0, 30.0), 1)
        forecast_rain = np.round(np.random.uniform(5.0, 25.0), 1)
        soil_moisture = np.round(np.random.uniform(35.0, 60.0), 1)
    elif scenario == "high":
        temp = np.round(np.random.uniform(24.0, 32.0), 1)
        humidity = np.round(np.random.uniform(68.0, 85.0), 1)
        wind = np.round(np.random.uniform(10.0, 24.0), 1)
        recent_rain = np.round(np.random.uniform(35.0, 75.0), 1)
        forecast_rain = np.round(np.random.uniform(28.0, 60.0), 1)
        soil_moisture = np.round(np.random.uniform(62.0, 80.0), 1)
    else:  # excess / flood risk
        temp = np.round(np.random.uniform(22.0, 30.0), 1)
        humidity = np.round(np.random.uniform(82.0, 98.0), 1)
        wind = np.round(np.random.uniform(14.0, 38.0), 1)
        recent_rain = np.round(np.random.uniform(80.0, 240.0), 1)
        forecast_rain = np.round(np.random.uniform(70.0, 190.0), 1)
        soil_moisture = np.round(np.random.uniform(80.0, 99.0), 1)

    # Reference Evapotranspiration (ET0) estimation via simplified FAO-56 Penman-Monteith
    et0_base = 0.0023 * (temp + 17.8) * np.sqrt(max(temp - 12.0, 1.0)) * 4.5
    wind_factor = 1.0 + (wind - 10.0) * 0.015
    humidity_factor = 1.0 + (50.0 - humidity) * 0.008
    et0_daily = max(et0_base * wind_factor * humidity_factor, 2.0)
    
    # 7-day crop water requirement (ETc in mm)
    kc = KC_TABLE[crop][stage]
    water_req_mm = round(et0_daily * kc * 7.0, 1)

    # Effective water availability calculation
    soil_ret = SOIL_FACTOR[soil]
    effective_rain = (0.35 * recent_rain) + (0.50 * forecast_rain)
    moisture_depth = ((soil_moisture - 20.0) / 80.0) * 20.0 * soil_ret
    water_available = max(effective_rain + max(moisture_depth, 0.0), 0.0)
    
    ratio = water_available / max(water_req_mm, 15.0)
    
    # Agronomic status classification
    if ratio < 0.60:
        water_status = "LOW WATER / WATER STRESS"
        stress_level = "HIGH" if ratio < 0.35 else "MODERATE"
        disease_stress = "Stomatal Closure & Wilting"
    elif ratio <= 1.45:
        water_status = "OPTIMAL WATER"
        stress_level = "LOW"
        disease_stress = "Healthy (No Stress)"
    elif ratio <= 2.30:
        water_status = "HIGH WATER"
        stress_level = "MODERATE"
        disease_stress = "Soil Aeration Stress (Mild Hypoxia)"
    else:  # EXCESS WATER / WATERLOGGING RISK
        water_status = "EXCESS WATER / WATERLOGGING RISK"
        stress_level = "SEVERE" if ratio > 3.2 or (soil in ["Clay", "Black Cotton Soil"] and ratio > 2.8) else "HIGH"
        
        # Determine specific excess-water disease/stress based on agronomic logic
        if stage in ["Sowing", "Vegetative"] and soil_moisture > 88:
            disease_stress = "Damping Off Fungal Infection"
        elif humidity > 85 and temp >= 24:
            disease_stress = "Fungal Sheath & Leaf Blight"
        elif soil in ["Sandy", "Loam"] and recent_rain > 120:
            disease_stress = "Nitrogen & Nutrient Leaching Stress"
        elif soil in ["Clay", "Black Cotton Soil"] or soil_moisture > 90:
            disease_stress = "Pythium & Phytophthora Root Rot"
        else:
            disease_stress = "Waterlogging & Oxygen Depletion (Hypoxia)"

    # Look up treatment info
    t_info = TREATMENT_LOOKUP[disease_stress]
    treatment_name = t_info["treatment"]
    treatment_category = t_info["category"]
    active_ingredient = t_info["active_ingredient"]
    application_info = t_info["application_info"]

    # Recovery Outlook Modeling (based on stress severity, stage, and timely treatment)
    if disease_stress == "Healthy (No Stress)":
        recovery = "Full Recovery (90-100%)"
    elif disease_stress == "Stomatal Closure & Wilting":
        recovery = "Substantial Recovery (70-89%)" if stress_level == "MODERATE" else "Partial Recovery (50-69%)"
    elif disease_stress == "Soil Aeration Stress (Mild Hypoxia)":
        recovery = "Full Recovery (90-100%)"
    else:  # Excess water diseases
        if stage == "Harvesting":
            recovery = "Partial Recovery (50-69%)" if stress_level == "MODERATE" else "Low Recovery / Severe Loss (<50%)"
        elif stress_level == "HIGH":
            recovery = "Substantial Recovery (70-89%)"
        elif stress_level == "SEVERE":
            recovery = "Partial Recovery (50-69%)"
        else:
            recovery = "Substantial Recovery (70-89%)"

    records.append({
        "crop": crop,
        "growth_stage": stage,
        "soil_type": soil,
        "soil_moisture": soil_moisture,
        "recent_rainfall": recent_rain,
        "forecast_rainfall": forecast_rain,
        "temperature": temp,
        "humidity": humidity,
        "wind_speed": wind,
        "water_requirement_mm": water_req_mm,
        "water_status": water_status,
        "crop_stress_level": stress_level,
        "crop_disease_stress": disease_stress,
        "recommended_treatment": treatment_name,
        "treatment_category": treatment_category,
        "active_ingredient": active_ingredient,
        "application_info": application_info,
        "expected_recovery": recovery
    })

df = pd.DataFrame(records)
out_dir = os.path.join("data", "crop_water")
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "crop_water_requirement_data.csv")
df.to_csv(out_file, index=False)
print(f"Generated {len(df)} records in {out_file}")
print("\nWater Status distribution:")
print(df["water_status"].value_counts())
print("\nDisease/Stress distribution:")
print(df["crop_disease_stress"].value_counts())
print("\nRecommended Treatment distribution:")
print(df["recommended_treatment"].value_counts())
print("\nExpected Recovery distribution:")
print(df["expected_recovery"].value_counts())
