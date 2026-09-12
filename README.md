# GEMFORECAST AI — Professional Jeweller AI Platform
### Enterprise Diamond Verification, Evidence-Based Valuation, Real Comparables & Jeweller Intelligence

[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.1-black.svg)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn%201.6-orange.svg)](https://scikit-learn.org/)
[![SHAP](https://img.shields.io/badge/Explainable%20AI-SHAP-brightgreen.svg)](https://shap.readthedocs.io/)
[![Dataset](https://img.shields.io/badge/Verified%20Sales%20Records-193%2C573-blueviolet.svg)](#historical-benchmark-dataset)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 💎 Executive Summary

**GemForecast AI** is a production-grade diamond intelligence and appraisal workstation for jewellery professionals, wholesale traders, and gemologists. It transforms conventional single-point regression models into a transparent, **multi-pillar evidence-based valuation platform** grounded in real gemological data and official verification standards.

### 🏛️ Core Multi-Pillar Valuation Architecture

```
                                  [ GIA Certificate / PDF / 4Cs Input ]
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │   GIA Verification Workflow   │
                                    │  (Official GIA Report Check)  │
                                    └───────────────┬───────────────┘
                                                    │
                   ┌────────────────────────────────┼────────────────────────────────┐
                   ▼                                ▼                                ▼
   ┌───────────────────────────────┐┌───────────────────────────────┐┌───────────────────────────────┐
   │           PILLAR 1            ││           PILLAR 2            ││           PILLAR 3            │
   │      Historical ML Model      ││   Real Database Comparables   ││   Wholesale Market Feed API   │
   │  (193.5k Benchmark + SHAP)   ││    (193,573 Verified Sales)   ││  (RapNet / IDEX / Polygon)   │
   │  • R² = 0.936, MAE = $568     ││  • Empirical Median & P25-P75 ││  • Connected Feed or Explicit │
   │  • Feature Attribution (XAI)  ││  • Dynamic Similarity Score   ││    "Not Connected" Status    │
   └───────────────┬───────────────┘└───────────────┬───────────────┘└───────────────┬───────────────┘
                   │                                │                                │
                   └────────────────────────────────┼────────────────────────────────┘
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │   Valuation Synthesis &      │
                                    │   Confidence Scoring (0-100)  │
                                    └───────────────┬───────────────┘
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │   Jeweller Margin & Deal      │
                                    │   Analytics & Formal Dossier  │
                                    └───────────────────────────────┘
```

---

## 🚀 Key Features & Capabilities

### 1. GIA Certificate Ingestion & Official Verification
- **Automated PDF Parsing**: Uses `pypdf` to extract report number, date, origin type (Natural vs Lab-Grown), shape, 4Cs, proportions (Table %, Depth %), millimeter dimensions ($X \times Y \times Z$), Polish, Symmetry, and Fluorescence.
- **Official GIA Verification Workflow**: Generates direct deep links to the official **GIA Report Check Portal** (`https://www.gia.edu/report-check?reportno=...`).
- **Strict Real-Data Policy**: Never fakes or simulates verification status. If an API key is unconfigured, clearly displays portal readiness without false claims.

### 2. Real Database Comparables Engine (193,573 Records)
- Vectorized $k$-nearest query over the 193,573 verified historical sales records in `artifacts/train.csv` / `raw.csv`.
- Filters diamonds within tight tolerance ($Carat \pm 12\%$, matching Cut, Color, Clarity, Table/Depth geometry).
- Calculates empirical price distributions (Min, P25, Median, P75, Max, Average Price/Carat).
- Explicitly labels data as **Historical Benchmark Comparables**, avoiding misrepresentation as "live" quotes.

### 3. Historical ML Valuation Model & SHAP Explainable AI
- Pre-trained Ridge/Linear ensemble regression pipeline (`best_model.pkl` + `preprocessor.pkl`).
- R²: **0.936** | MAE: **$568.20** | Training Dataset: **193,573 records**.
- SHAP (SHapley Additive exPlanations) generates exact dollar attribution for each diamond characteristic (Carat, Color, Clarity, Cut, Dimensions).

### 4. Jeweller Commercial Margin & Deal Economics
- Evaluates asking / memo price against estimated fair market value.
- Computes gross margin ($ and %), deal rating (*Exceptional Wholesale Deal*, *Fair Market Range*, *Retail Premium*), and recommended retail price with standard markup curves (25% to 50%).

### 5. Jeweller Workspace & Inventory Store
- Persistent local SQLite database (`artifacts/jeweller_workspace.db`).
- Manage in-stock inventory, client memo consignments, and appraisal history logs.
- Side-by-side **Comparison Matrix** for up to 4 diamonds.

### 6. Domain AI Gemologist & Proportion Analyzer
- Evaluates physical diamond proportions against **Tolkowsky Ideal (1919)** and **GIA Excellent** standards (Table 54–57%, Depth 61–62.5%, Ratio 1.00–1.02).
- Expert gemological advisory for magic carat size cliffs, fluorescence impact on D-F vs I-J diamonds, and natural vs lab-grown trading spreads.

---

## 🛠️ Project Structure

```
├── app.py                          # Flask application & routing layer
├── artifacts/                      # Model pickles, benchmark dataset, SQLite DB
│   ├── best_model.pkl              # Historical ML regression model
│   ├── preprocessor.pkl            # ColumnTransformer & OrdinalEncoder
│   ├── raw.csv                     # 193,573 verified diamond sales records
│   ├── train.csv                   # Training partition
│   └── jeweller_workspace.db       # Local persistent workspace database
├── src/
│   └── DiamondPricePrediction/
│       ├── component/              # Ingestion, transformation & training components
│       ├── pipeline/
│       │   ├── prediction.py       # PredictionPipeline & SHAP attribution
│       │   └── training.py         # Model training pipeline
│       ├── services/               # Production business logic layer
│       │   ├── gia_service.py      # GIA PDF extraction & verification service
│       │   ├── market_data_service.py # Wholesale B2B provider layer
│       │   ├── comparables_service.py # 193.5k dataset comp search engine
│       │   ├── valuation_engine.py # Multi-pillar synthesis & deal engine
│       │   ├── inventory_service.py # Local SQLite storage service
│       │   └── ai_assistant_service.py # Domain AI & proportion evaluator
│       └── utils/
├── static/
│   ├── css/gemforecast.css         # Luxury jeweller design system & print styles
│   └── js/gemforecast.js           # Client-side validation & utilities
├── templates/                      # UI templates (Dark luxury B2B theme)
│   ├── index.html                  # Platform landing page
│   ├── form.html                   # Diamond appraisal & GIA entry portal
│   ├── result.html                 # Formal Valuation & Verification Dossier
│   ├── inventory.html              # Jeweller inventory workspace
│   ├── compare.html                # Multi-diamond comparison matrix
│   ├── market_settings.html        # Market API credentials manager
│   └── assistant.html              # AI Gemologist & Proportion Calculator
├── tests/
│   └── test_gemforecast.py         # Pytest automated test suite
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Virtual Environment recommended

### 2. Installation
```powershell
# Clone the repository
git clone https://github.com/Anshgallery/Diamond_price_prediction_project.git
cd Diamond_price_prediction_project

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Automated Tests
```powershell
pytest tests/test_gemforecast.py
```

### 4. Launch Web Application
```powershell
python app.py
```
Open your browser and navigate to: **[http://127.0.0.1:8080](http://127.0.0.1:8080)**

---

## 📖 Diamond Gemology & Valuation Principles

### The 4Cs Hierarchy & Exponential Value Curves
1. **Carat Weight**: Prices scale exponentially, not linearly, with weight due to rarity. Key psychological price cliffs occur at **0.50 ct, 1.00 ct, 1.50 ct, 2.00 ct, and 3.00 ct**.
2. **Cut Quality**: The single most critical driver of visual brilliance and light return. Tolkowsky Ideal proportions (54-57% Table, 61-62.5% Depth) ensure maximum total internal reflection.
3. **Color Grade (D–Z)**: D-F (Colorless) commands high rarity premiums; I-J trades at noticeable discounts but provides strong value for yellow gold settings.
4. **Clarity Grade (FL–I3)**: FL/IF represents investment rarity; VS1/VS2 is the sweet spot for eye-clean consumer luxury.

---

## 🔒 Strict Real-Data Governance

- **Zero Synthetic Market Prices**: Live market states remain strictly labeled as **"Not Connected"** unless authenticated API credentials (RapNet / IDEX / Polygon) are provided.
- **Zero Fabricated Verification**: Official GIA verification uses direct links to the official GIA database.
- **Auditable Benchmark Records**: All database comparables are derived from 193,573 real diamond records.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
