# GEMFORECAST IGI — India-First Jeweller AI Diamond Valuation Platform
### Official IGI Verification, Real Indian ₹ Market Benchmarks, Separate Natural vs. Lab-Grown Valuation & Jeweller Workspace

[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.1-black.svg)](https://flask.palletsprojects.com/)
[![IGI Verified](https://img.shields.io/badge/Certification-IGI%20Only-gold.svg)](https://lookup.igi.org/index.php/reports/diamond-reports/en)
[![Currency](https://img.shields.io/badge/Market%20Currency-Indian%20Rupee%20%28%E2%82%B9%29-green.svg)](#indian-diamond-wholesale-rates)
[![Hubs](https://img.shields.io/badge/Bourses-Mumbai%20BDB%20%7C%20Surat%20SDB-orange.svg)](#indian-diamond-wholesale-rates)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 💎 Executive Summary

**GemForecast IGI** is a production-grade, India-first diamond valuation and deal intelligence workstation designed specifically for **Indian retail jewellers, wholesale traders, and gemologists**. Focused exclusively on the **International Gemological Institute (IGI)**, it replaces manual 4C estimation with trusted IGI report verification, automated certificate PDF extraction, and live **Indian Rupee (₹)** wholesale market benchmarks calibrated to the **Bharat Diamond Bourse (Mumbai)** and **Surat Diamond Bourse (LGD Hub)**.

---

## 🏛️ Core System Architecture

```
                       [ IGI Report Number OR IGI Certificate PDF ]
                                            │
                                            ▼
                            ┌───────────────────────────────┐
                            │   Official IGI Verification   │
                            │ (lookup.igi.org / PDF OCR)   │
                            └───────────────┬───────────────┘
                                            │
                                            ▼
                            ┌───────────────────────────────┐
                            │ AI Gemological Normalization  │
                            │ (Identifies Natural vs. LGD)  │
                            └───────┬───────────────┬───────┘
                                    │               │
        ┌───────────────────────────┘               └───────────────────────────┐
        ▼                                                                       ▼
┌───────────────────────────────────────┐               ┌───────────────────────────────────────┐
│     NATURAL DIAMOND PRICING ENGINE    │               │    LAB-GROWN (LGD) PRICING ENGINE     │
│  • Mumbai Bharat Diamond Bourse (BDB) │               │  • Surat Diamond Bourse (SDB) CVD/HPHT│
│  • Rarity & Magic Carat Jumps (1ct+)  │               │  • Per-Carat Manufacturing Index      │
│  • 193.5k Historical Benchmark (₹)    │               │  • Fast Liquidity & Depreciating Curve│
└───────────────────┬───────────────────┘               └───────────────────┬───────────────────┘
                    │                                                       │
                    └───────────────────────────┬───────────────────────────┘
                                                ▼
                                ┌───────────────────────────────┐
                                │    Jeweller Business Decisions│
                                │  • Wholesale Fair Value (₹)   │
                                │  • Suggested Jeweller Buy (₹) │
                                │  • Suggested Customer Sell (₹)│
                                │  • Expected Profit & Margin % │
                                │  • 3% Diamond GST Invoice     │
                                │  • "Why This Price?" AI Note  │
                                └───────────────┬───────────────┘
                                                ▼
                                ┌───────────────────────────────┐
                                │   Secure Jeweller Workspace   │
                                │  (Inventory, 5-Report Compare,│
                                │   Trade Advisor, Calculator)  │
                                └───────────────────────────────┘
```

---

## 🚀 Key Features & Capabilities

### 1. IGI Verification & Certificate Extraction
- **IGI-Only Dedicated Workflow**: Official report check links generated for all reports (`https://lookup.igi.org/index.php/reports/diamond-reports/en?report_no=...`).
- **Automated PDF Parsing**: Upload any IGI Natural or Lab-Grown certificate PDF to automatically extract Report #, Origin, Carat, Color, Clarity, Cut, Proportions (Table %, Depth %), Polish, Symmetry, Fluorescence, and Laser Inscription.
- **Strict Real-Data Policy**: Never fakes verification status or bypasses CAPTCHA; transparently marks "Verified via IGI API", "Official IGI Portal Link Ready", or "Extracted from Certificate PDF".

### 2. Dual Valuation Engine (Natural vs. Lab-Grown)
- **Natural Diamonds**: Grounded in Mumbai BDB trade benchmarks, exponential carat thresholds, colorlessness premiums (D-F), eye-clean clarity tiers, and 193.5k historical sales data.
- **Lab-Grown Diamonds (LGD)**: Grounded in Surat CVD/HPHT wholesale manufacturing matrices (typically ₹9,000–₹48,000/ct), separate margin expectations, and rapid inventory turnover curves.

### 3. Jeweller Actionable Financial Metrics
- **Wholesale Fair Market Value (₹)** & Estimated Range (₹ Low – High).
- **Suggested Jeweller Buy (₹)**: Target wholesale acquisition price.
- **Suggested Customer Sell (₹)**: Fair retail quote with standard markup.
- **Expected Jeweller Gross Profit (₹)** & Gross Margin (%).
- **3% Diamond GST (HSN 7102)**: Exact tax breakdown and final invoice total.
- **"Why This Price?" Summary**: Human-readable business explanation highlighting value drivers and optical light return.

### 4. 5-Report Multi-IGI Comparison Matrix (`/compare`)
- Compare up to 5 IGI reports side-by-side.
- AI automatically awards:
  - 🏆 **Overall Jeweller Pick**
  - 💎 **Best Gemological Quality**
  - 💰 **Best Value for Money**
  - 🎯 **Best Buy (Highest Profit Margin)**
  - 🔄 **Best Resale / Trade Liquidity**

### 5. Secure Jeweller Workspace & Inventory (`/workspace`)
- Password-hashed Jeweller authentication (`AuthService`).
- Local SQLite database persistence (`artifacts/jeweller_workspace.db`).
- Manage in-stock inventory, memo consignments, customer inquiries, and price watchlists.
- Portfolio summary dashboard (Total Stock Value in ₹ Lakhs, Total Cost, Expected Gross Profit).

### 6. Interactive AI Jeweller Trade Advisor (`/assistant`)
- Real-world conversational guidance for Indian trade questions (e.g. *"Can I buy a 1.5ct Natural at ₹4.5 Lakh?"*, *"What markup to keep for Lab-Grown solitaire rings?"*).
- **Tolkowsky Proportions Checker**: Analyzes Table %, Depth %, and L/W ratio against super-ideal optical physics standards.

### 7. Standalone Jeweller Profit, Gold & GST Calculator (`/calculator`)
- Custom parameters for diamond cost, gold metal purity (18K/14K/22K/Platinum), gold weight, making charges (₹/g), markup %, and 3% GST.

---

## 💻 Tech Stack

- **Backend**: Python 3.13+, Flask 3.1, SQLite3, Werkzeug Security (Password Hashing)
- **Data & ML**: Scikit-Learn 1.6, Pandas, NumPy, PyPDF
- **Frontend**: Vanilla HTML5 / CSS3 (India-First Luxury Obsidian & Gold Dark Mode), Vanilla JavaScript, Google Fonts (Outfit & Inter)
- **Testing**: PyTest

---

## 🏃 Quick Start & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Anshgallery/Diamond_price_prediction_project.git
cd Diamond_price_prediction_project
```

### 2. Activate Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run Automated Tests
```bash
pytest tests/
```

### 4. Start the Application
```bash
python app.py
```
Open your browser and navigate to **`http://127.0.0.1:8080`**.

---

## 🔑 Pre-Configured Demo Jeweller Account

| Credential | Value |
| :--- | :--- |
| **Email** | `jeweller@zaveribazaar.in` |
| **Password** | `jeweller123` |
| **Store** | Shree Ganesh Gems & Jewels (Mumbai / Zaveri Bazaar) |
| **GSTIN** | `27AABCS1429B1Z8` |

---

## ⚡ Built-in Test IGI Reports

| Report # | Type | Specs | Shape |
| :--- | :--- | :--- | :--- |
| **`584392810`** | Natural Mined | 1.02 ct • E / VVS1 • Ideal Cut | Round Brilliant |
| **`LG612345678`** | Lab-Grown (CVD) | 2.04 ct • D / VVS2 • Ideal Cut | Round Brilliant |
| **`602384912`** | Natural Mined | 1.51 ct • F / VS1 • 3EX Polish/Sym | Round Brilliant |
| **`LG598124095`** | Lab-Grown (HPHT) | 1.75 ct • E / VS1 • Excellent | Oval Brilliant |
| **`549210483`** | Natural Mined | 0.72 ct • G / SI1 • Very Good | Round Brilliant |

---

## 📜 License
MIT License. Developed for Indian Jewellery Professionals & Gemologists.
