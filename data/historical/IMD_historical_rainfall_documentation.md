# IMD Historical Rainfall Dataset Documentation

**Project:** KRISHIRAKSHA AI  
**Student Roll Number:** 231FA04291  
**Target Variable:** `heavy_rain_risk` (Binary: 0 = Normal/Light/Moderate, 1 = Heavy/Extreme)

---

## 1. Verified Data Sources & Provenance

1. **Primary Source:** India Meteorological Department (IMD) National Data Centre (NDC), Pune & IMD Open Data via National Data Portal (`data.gov.in`).
2. **Meteorological Stations:** District-level rainfall stations covering key vulnerable river basins and agricultural zones across India:
   - **Godavari & Krishna Basins:** Andhra Pradesh (Guntur, Krishna, East Godavari, Visakhapatnam), Telangana (Hyderabad, Khammam)
   - **Western Ghats & Coastal:** Kerala (Wayanad, Idukki, Ernakulam), Karnataka (Udupi, Dakshina Kannada, Kodagu), Maharashtra (Kolhapur, Ratnagiri, Pune)
   - **Brahmaputra Basin:** Assam (Kamrup, Dhemaji, Cachar)
   - **Ganga & Kosi Basins:** Bihar (Patna, Darbhanga, Supaul), Uttar Pradesh (Varanasi, Gorakhpur)
   - **Mahanadi Basin:** Odisha (Puri, Cuttack, Balasore)
   - **Cauvery Basin:** Tamil Nadu (Thanjavur, Cuddalore, Chennai)
   - **Western Arid & Semi-Arid:** Gujarat (Surat, Rajkot), Punjab (Ludhiana, Amritsar)
3. **Reanalysis & Surface Meteorological Harmonization:** Harmonized with ECMWF ERA5-Land reanalysis and IMD High-Resolution Gridded Daily Rainfall (0.25° x 0.25°) dataset for temperature, surface humidity, and wind speed parameters.

---

## 2. IMD Rainfall Severity Classification

According to the official India Meteorological Department classification standard:
| Category | 24-Hour Rainfall Range | System Heavy Rain Risk Label |
|---|---|---|
| Very Light Rain | 0.1 mm - 2.4 mm | 0 (Normal) |
| Light Rain | 2.5 mm - 7.5 mm | 0 (Normal) |
| Moderate Rain | 7.6 mm - 35.5 mm | 0 (Moderate) |
| Rather Heavy | 35.6 mm - 64.4 mm | 0 (Elevated) |
| **Heavy Rain** | **64.5 mm - 115.5 mm** | **1 (High Risk / Heavy Rain)** |
| **Very Heavy Rain** | **115.6 mm - 204.4 mm** | **1 (Severe Risk / Very Heavy)** |
| **Extremely Heavy Rain** | **>= 204.5 mm** | **1 (Catastrophic / Extremely Heavy)** |

---

## 3. Clear Distinction: ML Model vs. Risk Engine

> **CRITICAL SCIENTIFIC DISTINCTION:**
> - **The Machine Learning Model** predicts **Heavy Rain Risk (`heavy_rain_risk`)** based on atmospheric features (atmospheric pressure trend, relative humidity, temperature depression, wind shear, and multi-day antecedent rainfall accumulation).
> - **The Risk Engine** assesses **Flood & Waterlogging Risk** by combining:
>   1. ML Model Heavy Rain probability output
>   2. Official IMD District Weather Warning color (GREEN, YELLOW, ORANGE, RED)
>   3. 3-day and 7-day cumulative rainfall accumulation (soil saturation index)
>   4. 24-hour and 48-hour IMD quantitative precipitation forecast (QPF)
>   5. Historical extreme precipitation thresholds for that specific agro-climatic zone.

This avoids falsely conflating pure meteorological precipitation prediction with hydrological flood hydrodynamic modeling while providing highly actionable, verified early warnings to Indian farmers.
