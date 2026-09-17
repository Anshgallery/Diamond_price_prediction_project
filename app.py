import os
import sys
import json
from datetime import datetime, timezone
from flask import Flask, request, render_template, redirect, url_for, flash, session, make_response

from DiamondPricePrediction.utils.logger import logging
from DiamondPricePrediction.utils.exception import CustomException
from DiamondPricePrediction.pipeline.prediction import Customdata, PredictionPipeline
from DiamondPricePrediction.services.igi_service import IGIService
from DiamondPricePrediction.services.indian_market_service import IndianMarketService
from DiamondPricePrediction.services.comparables_service import ComparablesService
from DiamondPricePrediction.services.valuation_engine import ValuationEngine
from DiamondPricePrediction.services.inventory_service import InventoryService
from DiamondPricePrediction.services.auth_service import AuthService
from DiamondPricePrediction.services.ai_assistant_service import AIAssistantService

# ============================================================
# FLASK APPLICATION INITIALIZATION
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "jeweller-ai-mumbai-surat-2026-secret-key")

# Initialize database schemas & demo jeweller account
AuthService.init_users_table()
InventoryService.init_db()

# Pre-load Historical ML baseline pipeline
prediction_pipeline = PredictionPipeline()


# ============================================================
# 1. PLATFORM HOME / IGI APPRAISAL PORTAL
# ============================================================

@app.route("/")
def home_page():
    market_config = IndianMarketService.get_config()
    workspace_stats = InventoryService.get_summary_stats(
        jeweller_id=session.get("jeweller", {}).get("id", "default")
    )
    samples = IGIService.get_all_samples()
    return render_template(
        "index.html",
        market_config=market_config,
        workspace_stats=workspace_stats,
        samples=samples
    )


# ============================================================
# 2. SINGLE IGI DIAMOND VALUATION DOSSIER
# ============================================================

@app.route("/appraise", methods=["GET", "POST"])
def appraise():
    market_config = IndianMarketService.get_config()

    try:
        if request.method == "GET":
            report_num = request.args.get("report_number", "").strip()
            asking_price_raw = request.args.get("asking_price")
            pricing_pref = request.args.get("pricing_preference")
        else:
            report_num = request.form.get("report_number", "").strip()
            asking_price_raw = request.form.get("asking_price_inr")
            pricing_pref = request.form.get("pricing_preference")

        asking_price = float(asking_price_raw) if asking_price_raw and asking_price_raw.strip() else None

        if not report_num:
            flash("Please provide a valid IGI report number.", "warning")
            return redirect(url_for("home_page"))

        # 1. Fetch sample report data or default structure
        sample_spec = IGIService.get_sample_report(report_num)
        
        if sample_spec:
            diamond_spec = dict(sample_spec)
        else:
            # Check if Lab-Grown by prefix
            is_lab = report_num.upper().startswith("LG")
            diamond_spec = {
                "report_number": report_num,
                "origin_type": "Lab-Grown" if is_lab else "Natural",
                "growth_process": "CVD (Chemical Vapor Deposition)" if is_lab else "Geological / Mined",
                "shape": "Round Brilliant",
                "carat": 1.00,
                "color": "F",
                "clarity": "VS1",
                "cut": "Ideal",
                "polish": "Excellent",
                "symmetry": "Excellent",
                "fluorescence": "None",
                "depth": 61.8,
                "table": 57.0,
                "x": 6.46,
                "y": 6.49,
                "z": 4.00,
                "inscription": f"IGI {report_num}"
            }

        if asking_price is not None:
            diamond_spec["asking_price"] = asking_price

        # 2. IGI Official Verification Workflow
        igi_verification = IGIService.get_verification_info(report_num)

        # 3. Real Indian Wholesale Market Quote (BDB Mumbai / Surat SDB)
        market_quote = IndianMarketService.get_indian_wholesale_quote(diamond_spec)

        # 4. 193.5k Historical Benchmark Comparables in INR (₹)
        comps_data = ComparablesService.find_comparables(
            carat=float(diamond_spec.get("carat", 1.0)),
            cut=str(diamond_spec.get("cut", "Ideal")),
            color=str(diamond_spec.get("color", "F")),
            clarity=str(diamond_spec.get("clarity", "VS1")),
            depth=float(diamond_spec.get("depth", 61.8)),
            table=float(diamond_spec.get("table", 57.0)),
            max_results=6
        )

        # 5. Historical ML Regression Baseline
        custom_data_obj = Customdata(
            carat=float(diamond_spec.get("carat", 1.0)),
            depth=float(diamond_spec.get("depth", 61.8)),
            table=float(diamond_spec.get("table", 57.0)),
            x=float(diamond_spec.get("x", 6.46)),
            y=float(diamond_spec.get("y", 6.49)),
            z=float(diamond_spec.get("z", 4.00)),
            cut=str(diamond_spec.get("cut", "Ideal")),
            color=str(diamond_spec.get("color", "F")),
            clarity=str(diamond_spec.get("clarity", "VS1")),
            origin_type=str(diamond_spec.get("origin_type", "Natural")),
            report_number=report_num
        )
        features_df = custom_data_obj.get_data_as_dataframe()
        ml_pred_arr = prediction_pipeline.prediction(features_df)
        raw_ml_usd = float(ml_pred_arr[0])

        # 6. Composite Valuation, Suggested Buy, Suggested Sell, Profit & GST + AI Face Layer
        valuation = ValuationEngine.calculate_valuation(
            diamond_spec=diamond_spec,
            ml_prediction_usd=raw_ml_usd,
            comps_data=comps_data,
            market_quote_inr=market_quote,
            asking_price_inr=asking_price,
            pricing_preference=pricing_pref
        )

        timestamp_str = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p IST")

        return render_template(
            "appraise.html",
            diamond_spec=diamond_spec,
            diamond_spec_json=json.dumps(diamond_spec),
            valuation=valuation,
            valuation_json=json.dumps(valuation),
            igi_verification=igi_verification,
            comparables=comps_data,
            timestamp=timestamp_str,
            market_config=market_config
        )

    except Exception as e:
        logging.error(f"Error during diamond appraisal: {e}")
        flash(f"Appraisal error: {str(e)}", "danger")
        return redirect(url_for("home_page"))


# ============================================================
# 3. IGI CERTIFICATE PDF UPLOAD & PARSER ROUTE
# ============================================================

@app.route("/parse-igi-pdf", methods=["POST"])
def parse_igi_pdf():
    try:
        if "igi_pdf" not in request.files:
            flash("No PDF file provided.", "warning")
            return redirect(url_for("home_page"))

        file = request.files["igi_pdf"]
        if file.filename == "" or not file.filename.lower().endswith(".pdf"):
            flash("Please upload a valid .pdf IGI diamond certificate.", "warning")
            return redirect(url_for("home_page"))

        # Limit file size (10 MB max)
        pdf_bytes = file.read()
        if len(pdf_bytes) > 10 * 1024 * 1024:
            flash("PDF file size exceeds 10MB limit.", "danger")
            return redirect(url_for("home_page"))

        asking_price_raw = request.form.get("asking_price_inr") or request.form.get("asking_price")
        asking_price = float(asking_price_raw) if asking_price_raw and asking_price_raw.strip() else None
        pricing_pref = request.form.get("pricing_preference")

        # Extract diamond characteristics
        parsed_result = IGIService.extract_from_pdf(pdf_bytes)

        if "error" in parsed_result or not parsed_result.get("success"):
            flash(f"Unable to read IGI certificate PDF: {parsed_result.get('error', 'Invalid format')}", "danger")
            return redirect(url_for("home_page"))

        diamond_spec = parsed_result.get("normalized", {})
        report_num = diamond_spec.get("report_number", "Unspecified")
        if asking_price is not None:
            diamond_spec["asking_price"] = asking_price

        # Run valuation pipeline on extracted specs
        market_quote = IndianMarketService.get_indian_wholesale_quote(diamond_spec)
        comps_data = ComparablesService.find_comparables(
            carat=float(diamond_spec.get("carat", 1.0)),
            cut=str(diamond_spec.get("cut", "Ideal")),
            color=str(diamond_spec.get("color", "F")),
            clarity=str(diamond_spec.get("clarity", "VS1")),
            depth=float(diamond_spec.get("depth", 61.8)),
            table=float(diamond_spec.get("table", 57.0))
        )

        custom_data_obj = Customdata(
            carat=float(diamond_spec.get("carat", 1.0)),
            depth=float(diamond_spec.get("depth", 61.8)),
            table=float(diamond_spec.get("table", 57.0)),
            x=float(diamond_spec.get("x", 6.46)),
            y=float(diamond_spec.get("y", 6.49)),
            z=float(diamond_spec.get("z", 4.00)),
            cut=str(diamond_spec.get("cut", "Ideal")),
            color=str(diamond_spec.get("color", "F")),
            clarity=str(diamond_spec.get("clarity", "VS1")),
            origin_type=str(diamond_spec.get("origin_type", "Natural")),
            report_number=report_num
        )
        ml_pred_arr = prediction_pipeline.prediction(custom_data_obj.get_data_as_dataframe())
        raw_ml_usd = float(ml_pred_arr[0])

        valuation = ValuationEngine.calculate_valuation(
            diamond_spec=diamond_spec,
            ml_prediction_usd=raw_ml_usd,
            comps_data=comps_data,
            market_quote_inr=market_quote,
            asking_price_inr=asking_price,
            pricing_preference=pricing_pref
        )

        igi_verification = {
            "status": "Extracted from IGI Certificate PDF",
            "verified": True,
            "badge_class": "badge-success",
            "message": f"Successfully parsed and normalized IGI Certificate for Report #{report_num}.",
            "verification_method": "IGI PDF Certificate OCR / Extractor",
            "report_check_url": f"{IGIService.OFFICIAL_LOOKUP_BASE}?report_no={report_num}",
            "report_number": report_num
        }

        timestamp_str = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p IST")
        flash("IGI Certificate PDF successfully parsed & appraised.", "success")

        return render_template(
            "appraise.html",
            diamond_spec=diamond_spec,
            diamond_spec_json=json.dumps(diamond_spec),
            valuation=valuation,
            valuation_json=json.dumps(valuation),
            igi_verification=igi_verification,
            comparables=comps_data,
            timestamp=timestamp_str,
            market_config=IndianMarketService.get_config()
        )

    except Exception as e:
        logging.error(f"Error parsing IGI PDF: {e}")
        flash(f"PDF extraction error: {str(e)}", "danger")
        return redirect(url_for("home_page"))


# ============================================================
# 4. OFFICIAL IGI REPORT PDF GENERATION & DOWNLOAD ROUTES
# ============================================================

@app.route("/pdf/<report_number>")
def serve_igi_pdf(report_number):
    try:
        pdf_bytes = IGIService.generate_report_pdf(report_number)
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="IGI_{report_number}.pdf"'
        return response
    except Exception as e:
        logging.error(f"Error serving PDF for report {report_number}: {e}")
        return "PDF generation error", 500


@app.route("/download-pdf/<report_number>")
def download_igi_pdf(report_number):
    try:
        pdf_bytes = IGIService.generate_report_pdf(report_number)
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="IGI_{report_number}.pdf"'
        return response
    except Exception as e:
        logging.error(f"Error downloading PDF for report {report_number}: {e}")
        return "PDF generation error", 500



# ============================================================
# 4. 5-REPORT MULTI-IGI COMPARISON MATRIX
# ============================================================

@app.route("/compare", methods=["GET", "POST"])
def compare():
    try:
        report_list = []

        if request.method == "POST":
            for i in range(1, 6):
                val = request.form.get(f"rep{i}", "").strip()
                if val:
                    report_list.append(val)
        else:
            # Default or query param sample
            is_sample = request.args.get("sample") == "true"
            if is_sample:
                report_list = ["584392810", "LG612345678", "602384912", "LG598124095", "549210483"]
            else:
                report_list = ["584392810", "LG612345678"]

        # Run valuation pipeline for each report
        dossiers = []
        for rep_no in report_list:
            sample_spec = IGIService.get_sample_report(rep_no)
            if sample_spec:
                spec = dict(sample_spec)
            else:
                is_lab = rep_no.upper().startswith("LG")
                spec = {
                    "report_number": rep_no,
                    "origin_type": "Lab-Grown" if is_lab else "Natural",
                    "shape": "Round Brilliant",
                    "carat": 1.00,
                    "color": "F",
                    "clarity": "VS1",
                    "cut": "Ideal",
                    "depth": 61.8,
                    "table": 57.0,
                    "x": 6.46,
                    "y": 6.49,
                    "z": 4.00
                }

            market_quote = IndianMarketService.get_indian_wholesale_quote(spec)
            comps = ComparablesService.find_comparables(spec["carat"], spec["cut"], spec["color"], spec["clarity"])
            custom_d = Customdata(spec["carat"], spec["depth"], spec["table"], spec["x"], spec["y"], spec["z"], spec["cut"], spec["color"], spec["clarity"])
            ml_pred = float(prediction_pipeline.prediction(custom_d.get_data_as_dataframe())[0])
            val = ValuationEngine.calculate_valuation(spec, ml_pred, comps, market_quote)
            
            dossiers.append({
                "diamond_spec": spec,
                "valuation": val
            })

        # Synthesize 5-Report matrix and AI awards
        comparison = AIAssistantService.compare_5_reports(dossiers)

        return render_template(
            "compare.html",
            reports=report_list,
            comparison=comparison
        )

    except Exception as e:
        logging.error(f"Error in multi-report comparison: {e}")
        flash(f"Comparison error: {str(e)}", "danger")
        return redirect(url_for("home_page"))


# ============================================================
# 5. JEWELLER WORKSPACE & INVENTORY PORTFOLIO
# ============================================================

@app.route("/workspace")
def workspace():
    jeweller_id = session.get("jeweller", {}).get("id", "default")
    tag_filter = request.args.get("tag", "All")
    query = request.args.get("q", "")

    items = InventoryService.get_inventory(tag_filter=tag_filter, query=query, jeweller_id=jeweller_id)
    stats = InventoryService.get_summary_stats(jeweller_id=jeweller_id)

    return render_template(
        "workspace.html",
        items=items,
        stats=stats,
        current_tag=tag_filter,
        query=query
    )


@app.route("/inventory/save", methods=["POST"])
def save_to_inventory():
    try:
        jeweller_id = session.get("jeweller", {}).get("id", "default")
        spec_json = request.form.get("diamond_spec_json", "{}")
        val_json = request.form.get("valuation_json", "{}")
        tag = request.form.get("tag", "Inventory")
        buying_price = request.form.get("buying_price_inr")

        diamond_spec = json.loads(spec_json)
        valuation = json.loads(val_json)
        buy_val = float(buying_price) if buying_price and buying_price != "None" else None

        item_id = InventoryService.save_diamond(
            diamond_spec=diamond_spec,
            valuation_result=valuation,
            buying_price_inr=buy_val,
            status="In Stock" if tag == "Inventory" else tag,
            tag=tag,
            jeweller_id=jeweller_id
        )
        flash(f"Diamond #{diamond_spec.get('report_number')} saved to jeweller workspace.", "success")
        return redirect(url_for("workspace"))
    except Exception as e:
        logging.error(f"Error saving to workspace: {e}")
        flash("Failed to save diamond to workspace.", "danger")
        return redirect(url_for("workspace"))


@app.route("/inventory/save-to-workshop", methods=["POST"])
def save_to_workshop_action():
    try:
        jeweller_id = session.get("jeweller", {}).get("id", "default")
        spec_json = request.form.get("diamond_spec_json", "{}")
        val_json = request.form.get("valuation_json", "{}")
        buying_price = request.form.get("buying_price_inr")
        selling_price = request.form.get("selling_price_inr")

        diamond_spec = json.loads(spec_json)
        valuation = json.loads(val_json)
        
        buy_val = float(buying_price) if buying_price and buying_price != "None" else float(valuation.get("suggested_buy_price", 0))
        sell_val = float(selling_price) if selling_price and selling_price != "None" else float(valuation.get("suggested_sell_price", 0))
        
        if sell_val > 0:
            valuation["suggested_sell_price"] = sell_val
            valuation["suggested_sell_price_formatted"] = IndianMarketService.format_inr(sell_val)

        item_id = InventoryService.save_diamond(
            diamond_spec=diamond_spec,
            valuation_result=valuation,
            buying_price_inr=buy_val,
            status="In Workshop",
            tag="Workshop",
            notes="Directly Saved to Workshop via AI Trade Recommendation",
            jeweller_id=jeweller_id
        )
        
        profit_amt = sell_val - buy_val
        profit_formatted = IndianMarketService.format_inr(profit_amt)
        flash(f"🎉 Diamond #{diamond_spec.get('report_number')} ({diamond_spec.get('carat')} ct {diamond_spec.get('color')}/{diamond_spec.get('clarity')}) successfully saved to Workshop! (Expected Profit: {profit_formatted})", "success")
        return redirect(url_for("workspace", tag="Workshop"))
    except Exception as e:
        logging.error(f"Error saving diamond to workshop: {e}")
        flash("Failed to save diamond to workshop.", "danger")
        return redirect(url_for("workspace"))


@app.route("/workspace/view/<item_id>")
def view_workspace_item(item_id):
    item = InventoryService.get_diamond_by_id(item_id)
    if not item or not item.get("dossier"):
        flash("Diamond record not found.", "warning")
        return redirect(url_for("workspace"))

    dossier = item["dossier"]
    diamond_spec = dossier["diamond_spec"]
    valuation = dossier["valuation"]

    igi_verification = IGIService.get_verification_info(diamond_spec.get("report_number"))
    comps_data = ComparablesService.find_comparables(
        carat=float(diamond_spec.get("carat", 1.0)),
        cut=str(diamond_spec.get("cut", "Ideal")),
        color=str(diamond_spec.get("color", "F")),
        clarity=str(diamond_spec.get("clarity", "VS1")),
        depth=float(diamond_spec.get("depth", 61.8)),
        table=float(diamond_spec.get("table", 57.0))
    )

    return render_template(
        "appraise.html",
        diamond_spec=diamond_spec,
        diamond_spec_json=json.dumps(diamond_spec),
        valuation=valuation,
        valuation_json=json.dumps(valuation),
        igi_verification=igi_verification,
        comparables=comps_data,
        timestamp=item.get("created_at", "Saved Record"),
        market_config=IndianMarketService.get_config()
    )


@app.route("/workspace/delete/<item_id>", methods=["POST"])
def delete_workspace_item(item_id):
    InventoryService.delete_diamond(item_id)
    flash("Diamond removed from workspace.", "info")
    return redirect(url_for("workspace"))


# ============================================================
# 6. STANDALONE JEWELLER PROFIT & GST CALCULATOR
# ============================================================

@app.route("/calculator")
def calculator():
    market_config = IndianMarketService.get_config()
    return render_template("calculator.html", market_config=market_config)


# ============================================================
# 7. AI JEWELLER TRADE ADVISOR & PROPORTIONS
# ============================================================

@app.route("/assistant", methods=["GET", "POST"])
def assistant():
    response = None
    query = ""
    if request.method == "POST":
        query = request.form.get("query", "")
        if query:
            response = AIAssistantService.ask_assistant(query)

    return render_template(
        "assistant.html",
        query=query,
        response=response,
        prop_data={},
        prop_eval=None
    )


@app.route("/assistant/proportions", methods=["POST"])
def evaluate_proportions():
    table = float(request.form.get("table", 56.5))
    depth = float(request.form.get("depth", 61.8))
    x = float(request.form.get("x", 6.46))
    y = float(request.form.get("y", 6.49))
    z = float(request.form.get("z", 4.00))

    prop_eval = AIAssistantService.evaluate_proportions("Round Brilliant", table, depth, x, y, z)
    prop_data = {"table": table, "depth": depth, "x": x, "y": y, "z": z}

    return render_template(
        "assistant.html",
        query="",
        response=None,
        prop_data=prop_data,
        prop_eval=prop_eval
    )


# ============================================================
# 8. INDIAN WHOLESALE MARKET RATES & CONFIG
# ============================================================

@app.route("/market-rates", methods=["GET", "POST"])
def market_rates():
    if request.method == "POST":
        usd_inr = float(request.form.get("usd_inr_rate", 87.5))
        provider = request.form.get("provider", "Bharat Diamond Bourse (BDB) Wholesale")
        api_key = request.form.get("api_key", "").strip()
        igi_key = request.form.get("igi_api_key", "").strip()

        if igi_key:
            os.environ["IGI_API_KEY"] = igi_key

        IndianMarketService.save_config(usd_inr_rate=usd_inr, provider=provider, api_key=api_key)
        flash("Indian wholesale market settings updated.", "success")

    config = IndianMarketService.get_config()
    return render_template("market_rates.html", config=config)


# ============================================================
# 9. JEWELLER AUTHENTICATION (LOGIN, REGISTER, LOGOUT)
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        jeweller = AuthService.authenticate(email, password)
        if jeweller:
            session["jeweller"] = jeweller
            flash(f"Welcome back, {jeweller['owner_name']} ({jeweller['business_name']})!", "success")
            return redirect(url_for("workspace"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["POST"])
def register():
    business_name = request.form.get("business_name", "")
    owner_name = request.form.get("owner_name", "")
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    city = request.form.get("city", "Mumbai")
    gst = request.form.get("gst_number", "")

    result = AuthService.register_jeweller(business_name, owner_name, email, password, city, gst)
    if result.get("success"):
        session["jeweller"] = result["jeweller"]
        flash("Jeweller account registered successfully!", "success")
        return redirect(url_for("workspace"))
    else:
        flash(result.get("error", "Registration failed."), "danger")
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop("jeweller", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("home_page"))


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8080
    )