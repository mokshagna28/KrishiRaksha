# Dataset Documentation: Crop Water Requirement & Excess-Water Recovery Benchmark

**Dataset Title:** FAO-56 & ICAR Empirical Crop Water Requirement, Plant Pathology & Excess-Water Recovery Benchmark  
**Standard Reference:** Food and Agriculture Organization (FAO) Irrigation and Drainage Paper No. 56 (*Crop Evapotranspiration: Guidelines for computing crop water requirements* - Allen et al.) & Indian Council of Agricultural Research (ICAR) Directorate of Water Management & Plant Pathology Extension Handbooks.  
**Source Repository:** Curated from empirical crop water response tables, ICAR regional research stations (Andhra Pradesh, Maharashtra, Punjab, Karnataka, Tamil Nadu), and field pathology treatment efficacy benchmarks.

---

## 1. Dataset Overview

* **Dataset Name:** `crop_water_requirement_data.csv`
* **File Location:** `data/crop_water/crop_water_requirement_data.csv`
* **Total Records:** 4,000 observation records across major Indian agricultural zones.
* **License:** Creative Commons Attribution 4.0 International (CC BY 4.0) / Public Domain Agricultural Research Data.
* **Collection Scope:** Major Kharif, Rabi, and Zaid agricultural crops grown in peninsular and northern India (Rice/Paddy, Maize, Cotton, Wheat, Sugarcane, Pulses, Tomato).

---

## 2. Features Description

| Feature Name | Data Type | Units | Description | Typical Range |
|---|---|---|---|---|
| `crop` | Categorical | String | Primary crop cultivated | Rice, Cotton, Maize, Wheat, Sugarcane, Pulses, Tomato |
| `growth_stage` | Categorical | String | Phenological growth stage | Sowing, Vegetative, Flowering, Harvesting |
| `soil_type` | Categorical | String | Soil classification by texture & water retention | Clay, Loam, Sandy, Black Cotton Soil |
| `soil_moisture` | Numerical | % | Volumetric soil moisture content | 15% – 99% |
| `recent_rainfall` | Numerical | mm | Cumulative rainfall received over the past 7 days | 0 – 240 mm |
| `forecast_rainfall` | Numerical | mm | Expected rainfall over the next 24 to 48 hours | 0 – 190 mm |
| `temperature` | Numerical | °C | Mean ambient air temperature | 14°C – 42°C |
| `humidity` | Numerical | % | Mean relative atmospheric humidity | 25% – 98% |
| `wind_speed` | Numerical | km/h | 2-meter average horizontal wind velocity | 2 – 45 km/h |

---

## 3. Target Variables & Machine Learning Tasks

### A. Continuous Target (Regression)
* **Target:** `water_requirement_mm`
* **Units:** **mm/period** (Millimeters of water required for crop evapotranspiration during the growth stage under prevailing climatic conditions, calculated via FAO-56 Penman-Monteith method: $ET_c = K_c \times ET_0$).

### B. Water Status Classification
* **Target:** `water_status`
* **Classes:**
  1. `LOW WATER / WATER STRESS`: Water deficit where effective available water is substantially below crop evapotranspiration requirement.
  2. `OPTIMAL WATER`: Effective water availability satisfies crop evapotranspiration demand within healthy field capacity.
  3. `HIGH WATER`: Water availability exceeds evapotranspiration requirement.
  4. `EXCESS WATER / WATERLOGGING RISK`: Water supply exceeds field capacity and soil porosity, resulting in root hypoxia, nutrient leaching, and flood damage.

### C. Secondary Stress Indicator
* **Target:** `crop_stress_level`
* **Classes:** `LOW`, `MODERATE`, `HIGH`, `SEVERE`.

### D. Excess-Water Disease / Stress Identification (Classification)
* **Target:** `crop_disease_stress`
* **Classes:**
  - `Healthy (No Stress)`
  - `Stomatal Closure & Wilting`
  - `Soil Aeration Stress (Mild Hypoxia)`
  - `Waterlogging & Oxygen Depletion (Hypoxia)`
  - `Pythium & Phytophthora Root Rot`
  - `Fungal Sheath & Leaf Blight`
  - `Damping Off Fungal Infection`
  - `Nitrogen & Nutrient Leaching Stress`

### E. Treatment & Pesticide Prediction (Classification)
* **Target:** `recommended_treatment`
* **Associated Metadata Fields:** `treatment_category`, `active_ingredient`, `application_info`
* **Learned Treatments:**
  - `No Chemical Treatment Needed (Maintain Normal Irrigation)`
  - `Supplemental Precision Irrigation + Anti-transpirant Spray`
  - `Surface Field Drainage + Soil Aeration Ridge Formation`
  - `Field Trench Drainage + Potassium Nitrate Foliar Spray (1%)`
  - `Carbendazim 50% WP + Metalaxyl-Mancozeb Drenching`
  - `Copper Oxychloride 50% WP + Hexaconazole Spray`
  - `Trichoderma Viride Bio-Fungicide Soil Application`
  - `Drainage Channel Clearing + Foliar Urea (1-2%) Spray`

### F. Expected Recovery Condition Prediction (Classification)
* **Target:** `expected_recovery`
* **Classes:**
  - `Full Recovery (90-100%)`
  - `Substantial Recovery (70-89%)`
  - `Partial Recovery (50-69%)`
  - `Low Recovery / Severe Loss (<50%)`

---

## 4. Model Benchmarking & Pipeline Mapping

| Machine Learning Task | Model Architecture Candidates | Primary Benchmark Metric |
|---|---|---|
| Water Requirement Prediction | Linear Regression, Random Forest Regressor, Gradient Boosting Regressor | MAE, RMSE, $R^2$ |
| Water Status Classification | Logistic Regression, Random Forest Classifier, Gradient Boosting Classifier | Accuracy, Precision, Recall, F1-Score |
| Disease/Stress Identification | Logistic Regression, Random Forest Classifier, Gradient Boosting Classifier | Accuracy, Precision, Recall, F1-Score |
| Recommended Treatment Prediction | Logistic Regression, Random Forest Classifier, Gradient Boosting Classifier | Accuracy, Precision, Recall, F1-Score |
| Expected Recovery Prediction | Logistic Regression, Random Forest Classifier, Gradient Boosting Classifier | Accuracy, Precision, Recall, F1-Score |

---

## 5. Scientific Safety & Regulatory Advisory

The predictions generated from this dataset are decision-support outputs based on ICAR package of practices and FAO-56 guidelines. All agrochemical treatments must be verified against product packaging, local agricultural university advisories, and national regulatory guidelines before field application.
