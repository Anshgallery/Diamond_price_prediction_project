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

### 7. Genuine Timestamped IBJA Gold & Silver Rates (`/api/ibja-rates`, `IBJAGoldService`)
- Official benchmark rates for **24K (999), 22K (916), 18K (750), 14K (585)**, and **Silver 999**.
- Dual daily market sessions (Opening AM & Closing PM) with transparent publication and fetch timestamps.
- **Strict Real Data Policy**: When network access is restricted or offline, transparently serves the verified official daily benchmark baseline (`is_live: false`). Never fakes real-time ticks.
- Exact Indian standard purity factors (e.g. 22K = 22/24 = 0.9167, 18K = 18/24 = 0.7500).

### 8. Licensed Natural & Verified Lab-Grown Pricing (`LicensedDiamondService`)
- **Licensed Natural Diamond Pricing**: Supports commercial `RAPNET_API_KEY` and `IDEX_API_KEY` configurations. When running in baseline mode, grounds pricing in the **Mumbai Bharat Diamond Bourse (BDB) physical trade benchmark matrix** with full source disclosure.
- **Verified Lab-Grown Diamond Pricing**: Grounded in the **Surat Diamond Bourse (SDB) CVD/HPHT wholesale manufacturing matrix** (~85%–97% discount to natural mined stones).
- **IGI Separation Notice**: Strict gemological separation: IGI certified reports evaluate physical 4C parameters; commercial valuation and trading appraisals are performed independently by GEMFORECAST.

### 9. High-Precision Decimal Jewellery Calculator & Quotation (`/calculator`, `JewelleryCalculator`)
- High-precision **Decimal arithmetic (`ROUND_HALF_UP`)** eliminating IEEE 754 floating-point inaccuracies.
- Calculates net metal cost, wastage %, diamond wholesale costs, gemstone additions, labour/making charges (per gram or flat), setting fees (per stone), and hallmarking (BIS ₹45).
- Taxable subtotal, retail markups, promotional discounts, and composite **3% Indian GST (HSN 7113: 1.5% CGST + 1.5% SGST or 3.0% IGST)**.
- Realized jeweller gross profit (₹), profit margin (%), and realized markup (%).

### 10. Saved Invoices, Bill History, Direct Print & PDF Downloads (`/invoices`, `InvoiceService`)
- **Persistent SQLite Invoice Storage**: Tracks customer name, phone, email, address, state, PAN, and itemized jewellery specifications.
- **Sequential Invoicing**: Automatic formatting (e.g., `GF-2026-0001`).
- **Cryptographic Share Links**: Each invoice receives a secure public share token (`/invoice/share/<token>`).
  - **Confidentiality Shield**: Public view strictly hides internal jeweller landed cost (`landed_cost`), margin %, and profit.
- **Direct Browser Print**: Native `@media print` CSS formats invoices cleanly on standard A4 paper, hiding browser UI, search bars, and navigation headers.
- **ReportLab PDF Generator (`InvoicePdfGenerator`)**: Generates official A4 tax invoices with jeweller header, customer KYC, HSN breakdown, dynamic QR code linking to verification URL, amount in Indian words, and signature block.

---

## 💻 Tech Stack

- **Backend**: Python 3.11+, Flask 3.1, SQLite3, Werkzeug Security, ReportLab 4.x
- **Data & ML**: Scikit-Learn 1.6, Pandas, NumPy, PyPDF
- **Frontend**: Vanilla HTML5 / CSS3 (India-First Luxury Obsidian & Gold Dark Mode), Vanilla JavaScript, Google Fonts (Outfit & Inter), Print CSS
- **Testing**: PyTest (35 Automated Tests)
- **Deployment**: Render (Docker / Gunicorn / Persistent Disk `/var/data`)

---

## 🏃 Quick Start & Installation

### 1. Clone the Repository & Configure Environment
```bash
git clone https://github.com/Anshgallery/Diamond_price_prediction_project.git
cd Diamond_price_prediction_project
cp .env.example .env
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
pytest tests/ -v
```

### 4. Start the Application Locally
```bash
python app.py
```
Open your browser and navigate to **`http://127.0.0.1:8080`**.

---

## ☁️ Production Deployment on Render

For step-by-step instructions with persistent disk storage (`/var/data`), see [DEPLOYMENT_RENDER.md](DEPLOYMENT_RENDER.md).

Quick Blueprint deployment:
1. Connect repository on [Render](https://dashboard.render.com).
2. Render detects [`render.yaml`](render.yaml) automatically.
3. Attaches persistent disk to `/var/data` so invoices and inventory survive all restarts.
4. Set optional `RAPNET_API_KEY`, `IDEX_API_KEY`, or `IBJA_API_KEY` in environment settings.

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

