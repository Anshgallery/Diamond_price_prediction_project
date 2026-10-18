# Deploying GEMFORECAST IGI to Render

This comprehensive guide covers deploying the **GEMFORECAST IGI** platform to [Render](https://render.com) with **persistent database storage**, secure environment variables, live market data feeds, and production-grade WSGI serving.

---

## 🏗️ Architecture on Render

When deployed to Render, GEMFORECAST runs as a Web Service backed by:
- **Python 3.11/3.13 Runtime** via Docker or Python native environment.
- **Gunicorn WSGI Server** (`gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 app:app`).
- **Persistent Disk (`/var/data`)**: Essential for SQLite database persistence (`jeweller_workspace.db`) across dyno restarts and redeployments.
- **Automatic SSL**: Render provisions automated TLS certificates for your domain.

---

## 🚀 Option 1: Blueprint Deployment via `render.yaml` (Recommended)

The repository includes a ready-to-use [`render.yaml`](render.yaml) blueprint.

### Step-by-Step Instructions:

1. **Push your code to GitHub**:
   Ensure your latest code with all invoices, IBJA feeds, and test suites is pushed to your GitHub repository.

2. **Open Render Dashboard**:
   Navigate to [dashboard.render.com](https://dashboard.render.com/) and click **New +** -> **Blueprint**.

3. **Connect Repository**:
   Select your `Diamond_price_prediction_project` repository.

4. **Review Blueprint Configuration**:
   Render will automatically detect [`render.yaml`](render.yaml) and configure:
   - **Service Name**: `gemforecast-igi`
   - **Environment**: `docker`
   - **Plan**: `starter` (Required for persistent disk)
   - **Disk Mount**:
     - Name: `gemforecast-data`
     - Mount Path: `/var/data`
     - Size: `1 GB` (or larger)
   - **Environment Variables**:
     - `DATABASE_PATH`: `/var/data/jeweller_workspace.db`
     - `PYTHONUNBUFFERED`: `1`
     - `SECRET_KEY`: Automatically generated cryptographically secure string

5. **Set Optional API Keys**:
   In the Environment tab, supply your commercial API keys if available:
   - `RAPNET_API_KEY`: *(Optional)* For live RapNet commercial diamond feed.
   - `IDEX_API_KEY`: *(Optional)* For live IDEX diamond exchange feed.
   - `IBJA_API_KEY`: *(Optional)* For proprietary commercial IBJA ticker feeds.

6. **Click Apply**:
   Render will build the Docker container, mount the persistent disk at `/var/data`, run database initialization, and launch the service.

---

## 🛠️ Option 2: Manual Web Service Deployment

If you prefer setting up the web service manually:

1. In Render, select **New +** -> **Web Service**.
2. Connect your repository.
3. Configure settings:
   - **Name**: `gemforecast-igi`
   - **Region**: Choose closest to target users (e.g., `Singapore` or `Frankfurt`).
   - **Branch**: `main`
   - **Runtime**: `Docker` (or `Python 3`)
     - If using *Python native*:
       - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
       - **Start Command**: `gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 app:app`
     - If using *Docker*:
       - Uses the production-hardened `Dockerfile` in the root directory.
   - **Instance Type**: `Starter` (to enable Disks).
4. **Attach Persistent Disk**:
   - Go to **Disks** section in settings.
   - Click **Add Disk**:
     - **Name**: `gemforecast-data`
     - **Mount Path**: `/var/data`
     - **Size**: `1 GB`
5. **Add Environment Variables**:
   ```ini
   PYTHONUNBUFFERED=1
   SECRET_KEY=generate_a_random_64_character_hex_key
   DATABASE_PATH=/var/data/jeweller_workspace.db
   ```
6. Click **Create Web Service**.

---

## 🔒 Persistent Database & Data Integrity

> [!IMPORTANT]
> Render Web Services have ephemeral container filesystems by default. Without an attached disk, any invoices, inventory items, or valuation logs stored in SQLite would be lost upon restart or redeployment.

By configuring:
```ini
DATABASE_PATH=/var/data/jeweller_workspace.db
```
The application stores:
- `invoices`: Saved GST tax invoices, customer KYC records, and share tokens.
- `inventory`: Jeweller workshop stock and memo items.
- `valuation_logs`: Audit trail of historical valuations.
- `jewellers`: Registered jeweller profiles and password hashes.

All data resides safely on the persistent `/var/data` mount and survives all restarts.

---

## 📡 Live Market Data, Freshness & Fallbacks

GEMFORECAST adheres to a strict **"Never Fake Live Data"** engineering principle.

### 1. IBJA Gold & Silver Rates
- **Source**: India Bullion and Jewellers Association (IBJA).
- **Update Frequency**: Published twice daily (Opening AM session ~11:30 AM IST, Closing PM session ~4:30 PM IST), excluding Sundays and national holidays.
- **Cache TTL**: In-memory and disk cache with 15-minute TTL to respect IBJA servers.
- **Fallback Behavior**:
  If Render's outbound network to external portals experiences latency or IP filtering:
  - The service automatically serves the **verified official daily benchmark baseline** (e.g., ₹7,850/g for 24K, ₹92.50/g for Silver).
  - Explicitly returns `"is_live": false` and `"freshness": "Verified Official Daily Benchmark Baseline"`.
  - Displays transparent disclosure badges in the UI and PDF invoices.

### 2. Licensed Natural Diamond Pricing
- **Commercial Feeds**: Checks for `RAPNET_API_KEY` or `IDEX_API_KEY`.
- **Baseline Matrix**: When keys are not supplied, uses the **Mumbai Bharat Diamond Bourse (BDB) physical trade benchmark matrix**.
- **Transparency**: Every quote lists its exact source (`"source": "Mumbai Bharat Diamond Bourse (BDB) Physical Trade Benchmark Baseline"`) and includes a commercial licensing notice.

### 3. Verified Lab-Grown (LGD) Diamond Pricing
- **Source**: **Surat Diamond Bourse (SDB) CVD/HPHT Wholesale Manufacturing Matrix**.
- Reflects current wholesale manufacturing prices (85%–97% discount relative to natural mined stones).
- Differentiates CVD from HPHT growth methods.

---

## 🧾 Saved Invoices, Direct Print & PDF Downloads

- **Unique Share Token**: Generated via `secrets.token_urlsafe(18)`.
- **Confidentiality Guarantee**: The public share endpoint (`/invoice/share/<token>`) serves a customer-facing white-label view where internal jeweller costs (`landed_cost`), margins (`margin_pct`), and gross profit are **strictly stripped**.
- **Direct Browser Print**: Custom `@media print` CSS formats the invoice cleanly onto standard A4 paper, hiding navigation bars, toolbars, and buttons.
- **PDF Generation**: Powered by ReportLab, outputting clean vector PDFs with HSN tax breakdown (7113, 7102, 7103, 9988), amount in Indian words, and dynamic QR verification code.

---

## 🛡️ Pre-Flight Verification & Health Check

After deployment completes on Render:

1. **Verify Home Page**:
   ```bash
   curl -I https://gemforecast-igi.onrender.com/
   ```
   Should return `HTTP/2 200`.

2. **Verify Live IBJA Endpoint**:
   ```bash
   curl https://gemforecast-igi.onrender.com/api/ibja-rates
   ```
   Should return JSON with `rates`, `publication_timestamp`, and `freshness`.

3. **Verify Invoice & Database Path**:
   Access `/invoices` to confirm the database initialized on `/var/data/jeweller_workspace.db`.

---

## ⚠️ Known Limitations & API Access Guidelines

| Service | Mode | Limitation / Access Guideline |
| :--- | :--- | :--- |
| **IGI Verification** | Real Verification | Official IGI report check is linked to `lookup.igi.org`. OCR parsing extracts 4Cs from user-uploaded PDFs. We do not bypass IGI CAPTCHAs. |
| **IBJA Gold Rates** | Benchmark + Live | Official public broadcast scraped or benchmark baseline returned; commercial high-frequency websocket requires enterprise IBJA membership. |
| **Natural Diamonds** | Licensed / BDB Benchmark | RapNet/IDEX require commercial subscriber credentials. BDB matrix provides accurate physical Mumbai wholesale benchmark. |
| **Lab-Grown Diamonds** | SDB Matrix | Surat wholesale index updated periodically based on manufacturer price cuts. |
