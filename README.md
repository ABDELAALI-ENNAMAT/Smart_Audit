<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:002D59,50:005EB8,100:00A3E0&height=220&section=header&text=SmartAudit&fontSize=72&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Industrial%20Performance%20Intelligence%20System&descSize=18&descAlignY=55&descColor=E8EEF7" width="100%" />
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" /></a>
  <a href="#"><img src="https://img.shields.io/badge/streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" /></a>
  <a href="#"><img src="https://img.shields.io/badge/scikit--learn-1.3+-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white" /></a>
  <a href="#"><img src="https://img.shields.io/badge/xgboost-2.0+-006400?style=for-the-badge&logo=xgboost&logoColor=white" /></a>
  <a href="#"><img src="https://img.shields.io/badge/plotly-5.18+-3F4F75?style=for-the-badge&logo=plotly&logoColor=white" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2D7A52?style=for-the-badge" /></a>
</p>

<p align="center">
  <b>OEE Monitoring</b> · <b>Hidden Cost Analysis (ISEOR)</b> · <b>ML Prediction</b> · <b>Anomaly Detection</b> · <b>Budget Variance</b>
</p>

---

## Overview

**SmartAudit** is a full-stack industrial performance intelligence platform built with Streamlit. It combines real-time OEE monitoring, hidden cost quantification based on the ISEOR methodology (Savall & Zardet), and machine learning prediction into a unified decision-support system for management controllers.

Designed as a **PFA (Projet de Fin d'Année)** at **ENCG Agadir** (2025–2026), the application demonstrates how data science and socio-economic management theory converge to automate industrial performance analysis.

<br/>

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SmartAudit Platform                         │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────┤
│Dashboard │Prediction│  Hidden  │ Anomaly  │Benchmark │  Budget vs  │
│Executive │  OEE ML  │  Costs   │  Alerts  │ Compare  │   Réalisé   │
├──────────┴──────────┴──────────┴──────────┴──────────┴─────────────┤
│                     Streamlit Multi-Page App                       │
├────────────────┬────────────────┬───────────────────────────────────┤
│  Chart Builder │  UI Components │      Report Generator            │
│  (Plotly)      │  (HTML/SVG)    │      (PDF / Excel)               │
├────────────────┴────────────────┴───────────────────────────────────┤
│                        Core Engine Layer                           │
├──────────┬──────────┬───────────┬───────────────────────────────────┤
│   OEE    │ Hidden   │ Benchmark │        ML Pipeline               │
│  Calc    │  Cost    │  Engine   │  RF · XGBoost · Isolation Forest │
│(ISO22400)│ (ISEOR)  │ (Midpoint)│  5-Fold CV · Hyperparameter Opt  │
├──────────┴──────────┴───────────┴───────────────────────────────────┤
│                     Data Layer (pandas)                             │
│               CSV → Validation → Transformation                    │
└─────────────────────────────────────────────────────────────────────┘
```

<br/>

## Features

### Performance Monitoring
| Module | Description |
|--------|-------------|
| **Executive Dashboard** | Real-time OEE, production KPIs, trend analysis with 3-tab layout (Overview, Detailed Analysis, Steering) |
| **OEE Prediction** | ML-based OEE forecasting using Random Forest and XGBoost with feature importance analysis |
| **Hidden Costs** | ISEOR-based hidden cost quantification decomposed into availability, performance, and quality losses |
| **Anomaly Alerts** | Isolation Forest anomaly detection with structured action plans and responsibility mapping |
| **Benchmark** | Period-over-period comparison with midpoint OEE gap decomposition and automated narrative |
| **Budget vs Réalisé** | Variance analysis by responsibility center with controller commentary template |
| **Reports** | Automated PDF and Excel report generation with period filtering |

### Technical Highlights

- **OEE Calculation** — ISO 22400-2:2014 compliant (Availability × Performance × Quality)
- **Hidden Cost Model** — ISEOR methodology with margin coefficient (0.38) across three loss categories
- **ML Pipeline** — Chronological train/test split, 5-fold cross-validation, RandomizedSearchCV
- **Design System** — Corporate blue palette (#005EB8), Inter typography, WCAG-compliant contrast ratios
- **Currency Toggle** — MAD/EUR with live conversion (rate: 10.8)
- **PDF Reports** — Multi-page reports with KPI boxes, anomaly tables, and methodology appendix

<br/>

## Tech Stack

<table>
  <tr>
    <td align="center" width="110">
      <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="40" /><br/>
      <sub><b>Python</b></sub>
    </td>
    <td align="center" width="110">
      <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/streamlit/streamlit-original.svg" width="40" /><br/>
      <sub><b>Streamlit</b></sub>
    </td>
    <td align="center" width="110">
      <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/pandas/pandas-original.svg" width="40" /><br/>
      <sub><b>Pandas</b></sub>
    </td>
    <td align="center" width="110">
      <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/numpy/numpy-original.svg" width="40" /><br/>
      <sub><b>NumPy</b></sub>
    </td>
    <td align="center" width="110">
      <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/scikitlearn/scikitlearn-original.svg" width="40" /><br/>
      <sub><b>Scikit-learn</b></sub>
    </td>
    <td align="center" width="110">
      <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/plotly/plotly-original.svg" width="40" /><br/>
      <sub><b>Plotly</b></sub>
    </td>
    <td align="center" width="110">
      <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg" width="40" /><br/>
      <sub><b>Docker</b></sub>
    </td>
  </tr>
</table>

<br/>

## Quick Start

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/SmartAudit.git
cd SmartAudit

# Install dependencies
pip install -r requirements.txt

# Place your production data
cp your_data.csv data/production_data.csv

# Train ML models
python models/train_models.py

# Launch the application
streamlit run app.py
```

### Docker

```bash
docker compose up --build
# Open http://localhost:8501
```

<br/>

## Project Structure

```
SmartAudit/
├── app.py                          # Main entry point
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
├── docker-compose.yml              # Docker orchestration
├── Makefile                        # Build shortcuts
├── .env.example                    # Environment template
│
├── pages/                          # Streamlit multi-page modules
│   ├── 1_Dashboard.py              # Executive dashboard (3 tabs)
│   ├── 2_OEE_Prediction.py         # ML prediction interface
│   ├── 3_Hidden_Costs.py           # ISEOR hidden cost analysis
│   ├── 4_Anomaly_Alerts.py         # Anomaly detection & action plans
│   ├── 5_Benchmark.py              # Period comparison
│   ├── 7_Budget_vs_Realise.py      # Budget variance analysis
│   └── 8_Reports.py                # PDF/Excel report generation
│
├── utils/                          # Core business logic
│   ├── constants.py                # Shared constants & mappings
│   ├── data_loader.py              # Data loading, validation & theming
│   ├── oee_calculations.py         # OEE formulas (ISO 22400)
│   ├── benchmark_engine.py         # Comparative analysis engine
│   ├── chart_builder.py            # Plotly chart library (20+ charts)
│   ├── ui_helpers.py               # Reusable UI components
│   ├── report_generator.py         # PDF/Excel report builder
│   ├── methodology.py              # Academic methodology panel
│   └── icons.py                    # Lucide SVG icon system
│
├── models/                         # ML pipeline
│   └── train_models.py             # Training script (RF, XGBoost, IF)
│
├── assets/                         # Static assets
│   ├── design_tokens.py            # Design system (colors, radii, shadows)
│   ├── style.css                   # Custom CSS
│   ├── favicon.ico                 # Browser icon
│   └── company_logo.png            # Header logo
│
├── data/                           # Production data (gitignored)
│   └── production_data.csv         # Calibrated simulation dataset
│
└── .streamlit/
    └── config.toml                 # Streamlit theme configuration
```

<br/>

## Methodology

### OEE — ISO 22400-2:2014

```
OEE = Availability × Performance × Quality

Where:
  Availability = Operating Time / Planned Production Time
  Performance  = (Ideal Cycle Time × Units Produced) / Operating Time
  Quality      = Good Units / Units Produced

Classification:
  ≥ 85%  →  World Class
  ≥ 75%  →  On Target
  < 75%  →  Below Target
```

### Hidden Costs — ISEOR (Savall & Zardet)

The hidden cost model quantifies production losses in monetary terms:

| Loss Category | Formula |
|---------------|---------|
| **Availability** | `Lost Units × Revenue/Unit × Margin (0.38)` |
| **Performance** | `Speed Loss × Revenue/Unit × Margin × Speed Factor (0.5)` |
| **Quality** | `Rework Cost + Scrap Cost` |

### ML Pipeline

| Component | Method |
|-----------|--------|
| OEE Prediction | Random Forest + XGBoost ensemble |
| Hyperparameter Tuning | RandomizedSearchCV (5-fold CV) |
| Anomaly Detection | Isolation Forest (contamination = 5%) |
| Validation | Chronological train/test split (no data leakage) |
| Feature Engineering | Lag features, rolling averages, interaction terms |

<br/>

## Data

The dataset is a **calibrated simulation** built from:

1. **Documentary observation** — Production reports from an automotive wiring plant
2. **Semi-structured interviews** — Qualitative parameters from production and quality managers
3. **Calibrated generation** — Synthetic data aligned with industry benchmarks (AIAG, ISEOR, ISO 22400)

| Indicator | Simulated Range | Industry Reference |
|-----------|----------------|-------------------|
| OEE (automotive wiring) | 72–78% | AIAG 2023: 70–80% |
| Absenteeism rate | 4–7% | ISEOR: 4–8% |
| Defect rate (DPU) | 0.5–2% | Lean benchmark: < 2% |
| Machine availability | 80–90% | TPM world-class: > 90% |

<br/>

## Academic Context

| | |
|---|---|
| **Program** | PFA — ENCG Agadir 2025–2026 |
| **Field** | Management Control (Contrôle de Gestion) |
| **Approach** | Decision Support System for Industrial Performance |
| **Frameworks** | ISO 22400, ISEOR Socio-Economic Approach, AIAG |
| **References** | Savall & Zardet (ISEOR), Yin R.K. (Case Study Research, 2003), Thiétart R.A. (Méthodes de Recherche en Management, 2014) |

<br/>

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:002D59,50:005EB8,100:00A3E0&height=100&section=footer" width="100%" />
</p>
