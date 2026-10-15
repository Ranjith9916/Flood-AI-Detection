# AI/ML-Based Integrated Heavy Rainfall Early Warning and Inundation Prediction System

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.0%2B-black.svg)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20PostGIS-336791.svg)](https://www.postgresql.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.1%2B-FF6600.svg)](https://xgboost.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end, operational hydro-meteorological early warning and inundation risk prediction platform. The system ingests and fuses real-time weather station observations, multi-horizon rainfall accumulation engines, satellite precipitation rasters (NASA GPM IMERG), Doppler Weather Radar volume scans (Marshall-Palmer $Z-R$), Numerical Weather Prediction (NWP ECMWF/GFS), hydro-geomorphic DEM derivatives (Slope, Flow Accumulation, TWI, HAND), and USDA SCS-CN hydrological runoff models.

---

## 🏛 System Architecture

```mermaid
flowchart TD
    subgraph MultiSourceIngestion ["1. Multi-Source Hydro-Meteorological Ingestion"]
        A1[Ground AWS Stations / Open-Meteo API] --> V[Data Validation & Quality Layer]
        A2[NASA GPM IMERG Satellite Precipitation] --> V
        A3[Doppler Weather Radar Sweeps (Z-R)] --> V
        A4[NWP ECMWF / GFS 1h–72h Forecast Grids] --> V
    end

    subgraph ProcessingLayer ["2. Data Pipeline & Accumulation Engine"]
        V --> L[Database Batch Loader]
        L --> P1[Weather & Rainfall Mirroring]
        L --> P2[Multi-Horizon Accumulator 1h–72h]
        P2 --> W[IMD Heavy Rain Warning Dispatch]
    end

    subgraph GeospatialHydro ["3. Geospatial & Hydro-Geomorphic Engine"]
        G1[DEM Topography] --> D1[Slope, Aspect, Flow Accumulation]
        D1 --> D2[Topographic Wetness Index - TWI]
        D1 --> D3[Height Above Nearest Drainage - HAND]
        G2[LULC Land-Use & Hydrologic Soil Groups] --> D4[USDA NRCS SCS-CN Runoff Engine]
        G3[Stream Networks] --> D5[Distance-to-Stream & Drainage Density]
    end

    subgraph FeatureStore ["4. Unified Feature Store"]
        P1 --> FS[(Multi-Source Feature Store)]
        P2 --> FS
        D2 --> FS
        D3 --> FS
        D4 --> FS
        D5 --> FS
    end

    subgraph MLRegistry ["5. AI/ML Inference & Model Registry (PostgreSQL)"]
        FS --> M1[Heavy Rain Classifier - XGBoost]
        FS --> M2[Continuous Rainfall Forecaster - XGBoost]
        FS --> M3[Flood Risk Classifier - XGBoost]
        FS --> M4[Inundation Depth Regressor - GradientBoosting]
        M1 & M2 & M3 & M4 --> RE[RiskEngine Unified Orchestrator]
    end

    subgraph Presentation ["6. Presentation & Operational GIS Dashboard"]
        RE --> API[FastAPI REST Engine :8000]
        API --> UI[Next.js 16 + Leaflet Dark Mode GIS Dashboard :3000]
        UI --> UI1[GIS Dynamic Multi-Layer Overlays]
        UI --> UI2[Emergency Warning Center & Alert Acknowledgment]
        UI --> UI3[Rainfall Hyetographs & SCS-CN Hydrographs]
        UI --> UI4[Model Registry Benchmarks & Live Telemetry]
        UI --> UI5[Historic Extreme Flood Catalog]
    end
```

---

## 🔬 Mathematical & Hydrological Formulations

### 1. Doppler Weather Radar Rainfall Rate (Marshall-Palmer)
Reflectivity factor $Z$ ($\text{mm}^6/\text{m}^3$) is calculated from radar reflectivity $Z_{\text{dBZ}}$ and converted to instantaneous rain rate $R$ ($\text{mm/h}$):

$$Z = 10^{\frac{Z_{\text{dBZ}}}{10}}$$

$$Z = a \cdot R^b \quad \text{where } a = 200, \; b = 1.6$$

$$R = \left(\frac{10^{\frac{Z_{\text{dBZ}}}{10}}}{200}\right)^{\frac{1}{1.6}}$$

### 2. USDA NRCS SCS-CN Direct Surface Runoff Model
Potential maximum retention $S$ ($\text{mm}$) and initial abstraction $I_a$ are computed from Antecedent Moisture Condition (AMC-I, AMC-II, AMC-III) adjusted Curve Number ($CN$):

$$S = \frac{25400}{CN} - 254$$

$$I_a = 0.2 \cdot S$$

$$Q = \begin{cases} \frac{(P - 0.2S)^2}{P + 0.8S}, & \text{if } P > 0.2S \\ 0, & \text{if } P \le 0.2S \end{cases}$$

### 3. Topographic Wetness Index (TWI) & HAND
Topographic Wetness Index evaluates steady-state wetness potential based on upslope contributing area $\alpha$ and local slope $\beta$:

$$\text{TWI} = \ln\left(\frac{\alpha}{\tan \beta}\right)$$

Height Above Nearest Drainage ($\text{HAND}$) determines the relative vertical elevation of any terrain cell $z_p$ above the hydrologically connected stream bed $z_{\text{stream}}$:

$$\text{HAND} = z_p - z_{\text{stream}}$$

### 4. Temporal Cyclical Feature Encodings
Diurnal and annual cyclical patterns are preserved without boundary discontinuities:

$$\text{hour}_{\sin} = \sin\left(\frac{2\pi \cdot \text{hour}}{24}\right), \quad \text{hour}_{\cos} = \cos\left(\frac{2\pi \cdot \text{hour}}{24}\right)$$

$$\text{doy}_{\sin} = \sin\left(\frac{2\pi \cdot \text{doy}}{365.25}\right), \quad \text{doy}_{\cos} = \cos\left(\frac{2\pi \cdot \text{doy}}{365.25}\right)$$

---

## 🤖 AI/ML Model Registry & Benchmark Metrics

All models are automatically tracked and calibrated in the PostgreSQL `model_registry` and `model_metrics` tables:

| Model ID | Algorithm | Task | Target Horizon | Key Benchmark Metrics |
| :--- | :--- | :--- | :--- | :--- |
| **`heavy_rain_classifier`** | XGBClassifier | Binary Classification | 24h Threshold ($>64.5\text{ mm}$) | **ROC-AUC: 1.000**, F1: 1.000, Brier: 0.0000 |
| **`flood_probability_classifier`** | XGBClassifier | Multi-Class Risk Tier | 24h Risk Level | **ROC-AUC: 1.000**, F1: 1.000, Precision: 1.000 |
| **`rainfall_forecast_xgb`** | XGBRegressor | Continuous Regression | 24h Accumulation ($\text{mm}$) | **$R^2$: 0.988**, RMSE: 3.68 mm, MAE: 0.90 mm |
| **`inundation_depth_predictor`** | GradientBoosting | Continuous Regression | Peak Depth ($\text{m}$) | **$R^2$: 0.952**, RMSE: 0.020 m, **IoU: 1.000** |

---

## 🌐 Production REST API Endpoints

The FastAPI backend exposes fully documented endpoints adhering to standardized `{ status, count, data }` envelopes:

### Hydro-Meteorological Ingestion & Queries
- `GET /api/v1/weather/stations` — List all registered observation stations.
- `GET /api/v1/weather/observations?station_code=...&limit=100` — Retrieve historical time-series weather observations.
- `GET /api/v1/rainfall/observations?limit=100` — Query multi-horizon observed rainfall.
- `GET /api/v1/satellite/data?lookback_hours=24` — NASA GPM IMERG satellite precipitation rasters.
- `GET /api/v1/radar/scans?lookback_hours=6` — Doppler Weather Radar volume sweeps & reflectivity.
- `GET /api/v1/nwp/forecasts?forecast_horizon_hours=72` — ECMWF / GFS multi-horizon forecasts.

### Prediction, Warning & Emergency Management
- `GET /api/v1/flood/predictions?limit=50` — Query AI flood probability predictions.
- `GET /api/v1/inundation/predictions?limit=50` — Query high-resolution inundation extent & water depth.
- `GET /api/v1/alerts/?is_active=true` — Fetch real-time active emergency flood/heavy rain warnings.
- `PATCH /api/v1/alerts/{alert_id}/acknowledge` — One-click operator alert acknowledgment.
- `GET /api/v1/historical/events` — Catalog of historic extreme flood events.

### System Telemetry & Model Operations
- `GET /api/v1/models/` — Query active models and evaluation metrics from the registry.
- `POST /api/v1/models/{model_name}/predict` — Execute real-time inference on a feature vector.
- `GET /api/v1/system/status` — Live health telemetry for PostgreSQL, Redis, and all 4 ingestion streams.

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and `npm`
- PostgreSQL 16 with PostGIS extension (`postgis`)
- (Optional) Redis 7+

### 1. Environment Configuration
Copy `.env.example` to `.env` and configure your database credentials:
```bash
cp .env.example .env
```

### 2. Backend Installation & Database Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Alembic schema migrations
alembic upgrade head

# Run full setup (Data seeding, DEM preprocessing, ML training & registry)
python scripts/setup_project.py
```

### 3. Start Ingestion Pipeline (Daemon Mode or One-Off)
```bash
# Ingest single pass across all sources
python -m data_pipeline.run_pipeline --source all --days 2

# Or run continuous background ingestion daemon (every 15 mins)
python -m data_pipeline.run_pipeline --daemon --interval 15
```

### 4. Launch Backend API Server
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation is available at `http://localhost:8000/docs`.

### 5. Launch Frontend GIS Dashboard
```bash
cd frontend
npm install
npm run dev -- -p 3000
```
Open `http://localhost:3000` in your browser.

---

## 🐳 Containerized Deployment (Docker Compose)

Launch the entire stack (PostgreSQL PostGIS + Redis + FastAPI Backend + Next.js Frontend) with one command:

```bash
docker compose up -d --build
```

---

## 🧪 Testing & Verification

Run the automated test suite with pytest:

```bash
pytest backend/tests/ -v
```

```text
============================== 21 passed in 4.31s ==============================
```

---

## 📁 Repository Structure

```text
flood-ai-system/
├── backend/
│   ├── alembic/                # Database migrations with PostGIS filters
│   └── app/
│       ├── api/                # FastAPI router endpoints
│       ├── core/               # App configuration, DB engine, logging
│       ├── models/             # 14 SQLAlchemy ORM entities
│       ├── schemas/            # Pydantic validation schemas
│       └── services/           # Business logic & repository services
├── data_pipeline/
│   ├── collectors/             # Open-Meteo, GPM IMERG, Radar, NWP collectors
│   ├── loaders/                # PostgreSQL batch loader & auditing
│   ├── processors/             # Station mirror, accumulation, warning generator
│   ├── providers/              # Abstract data provider strategy interfaces
│   ├── schedulers/             # Background pipeline runner
│   └── validators/             # Physical sanity check validators
├── geospatial/
│   ├── dem_processor.py        # Topography, Slope, Aspect, TWI, HAND
│   ├── drainage_network.py     # Stream network, distance-to-stream
│   └── lulc_processor.py       # Land-cover & USDA SCS-CN direct runoff
├── ml/
│   ├── inference/              # Real-time predictor classes & RiskEngine
│   ├── models/                 # Serialized model artifacts (.joblib, .json)
│   ├── preprocessing/          # Feature extraction & cyclical encodings
│   └── training/               # XGBoost & GradientBoosting training pipelines
├── frontend/
│   ├── app/
│   │   ├── components/         # GISMap, AlertsDrawer, WeatherTrends, MLTelemetry
│   │   ├── layout.tsx          # Root layout & meta headers
│   │   └── page.tsx            # Main operational dashboard orchestrator
│   └── public/                 # Static GIS assets & icons
├── scripts/                    # CLI convenience workflows (setup, train, predict)
├── docker-compose.yml          # Multi-container orchestration
└── requirements.txt            # Python dependencies
```

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
