import os
import sys
import json
from datetime import datetime, timezone
from flask import Flask, request, render_template, redirect, url_for, flash, session, make_response, jsonify

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
from DiamondPricePrediction.services.ai_trade_advisor_agent import AITradeAdvisorAgent
from DiamondPricePrediction.services.ibja_gold_service import IBJAGoldService
from DiamondPricePrediction.services.licensed_diamond_service import LicensedDiamondService
from DiamondPricePrediction.services.jewellery_calculator import JewelleryCalculator
from DiamondPricePrediction.services.invoice_service import InvoiceService
from DiamondPricePrediction.services.invoice_pdf_generator import InvoicePdfGenerator
from DiamondPricePrediction.services.carathunter_service import CaratHunterService

# ============================================================
# FLASK APPLICATION INITIALIZATION
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "jeweller-ai-mumbai-surat-2026-secret-key")

# Initialize database schemas & demo jeweller account
AuthService.init_users_table()
InventoryService.init_db()
InvoiceService.init_db()
AITradeAdvisorAgent.init_db()

# Pre-load Historical ML baseline pipeline
prediction_pipeline = PredictionPipeline()

@app.context_processor
def inject_bullion_context():
    """Universally injects live Bullions.co.in & IBJA rates and market config across all templates."""
    rates = IBJAGoldService.get_current_rates()
    return {
        "bullion_rates": rates,
        "ibja_rates": rates,
        "market_config": IndianMarketService.get_config()
    }


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
# 6. STANDALONE JEWELLER PROFIT & GST CALCULATOR & INVOICES
# ============================================================

@app.route("/calculator")
def calculator():
    market_config = IndianMarketService.get_config()
    ibja_rates = IBJAGoldService.get_current_rates()
    return render_template("calculator.html", market_config=market_config, ibja_rates=ibja_rates)


@app.route("/api/ibja-rates")
@app.route("/api/bullion-rates")
def api_ibja_rates():
    """Live API endpoint for genuine timestamped Bullions.co.in & IBJA rates with auto-refresh support."""
    force = request.args.get("force", "false").lower() in ("true", "1", "yes")
    rates = IBJAGoldService.get_current_rates(force_refresh=force)
    resp = dict(rates)
    resp["success"] = True
    resp["rates_per_gram"] = {
        "24K": rates.get("rates", {}).get("24K", {}).get("rate_per_gram"),
        "22K": rates.get("rates", {}).get("22K", {}).get("rate_per_gram"),
        "18K": rates.get("rates", {}).get("18K", {}).get("rate_per_gram"),
        "14K": rates.get("rates", {}).get("14K", {}).get("rate_per_gram"),
        "Silver_999": rates.get("rates", {}).get("Silver_999", {}).get("rate_per_gram"),
        "Platinum_950": rates.get("rates", {}).get("Platinum_950", {}).get("rate_per_gram")
    }
    return jsonify(resp)


@app.route("/api/bullion/sync", methods=["GET", "POST"])
def api_bullion_sync():
    """Triggers on-demand synchronization with Bullions.co.in, returning fresh or STALE rates."""
    synced = IBJAGoldService.sync_on_login(force_refresh=True)
    resp = dict(synced)
    resp["success"] = True
    resp["synced"] = True
    resp["rates_per_gram"] = {
        "24K": synced.get("rates", {}).get("24K", {}).get("rate_per_gram"),
        "22K": synced.get("rates", {}).get("22K", {}).get("rate_per_gram"),
        "18K": synced.get("rates", {}).get("18K", {}).get("rate_per_gram"),
        "14K": synced.get("rates", {}).get("14K", {}).get("rate_per_gram"),
        "Silver_999": synced.get("rates", {}).get("Silver_999", {}).get("rate_per_gram"),
        "Platinum_950": synced.get("rates", {}).get("Platinum_950", {}).get("rate_per_gram")
    }
    return jsonify(resp)



@app.route("/api/calculate-jewellery", methods=["POST"])
def api_calculate_jewellery():
    """API endpoint for Decimal-precision jewellery quotation."""
    try:
        data = request.get_json() or request.form.to_dict()
        res = JewelleryCalculator.calculate(data)
        return jsonify({"success": True, "data": res})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/invoice/create", methods=["POST"])
def create_invoice_route():
    """Create and persist GST tax invoice with unique share link."""
    try:
        jeweller_id = session.get("jeweller", {}).get("id", "default")
        form_data = request.form.to_dict()
        res = InvoiceService.create_invoice(form_data, jeweller_id=jeweller_id)
        if res.get("success"):
            flash(f"Tax Invoice #{res['invoice_number']} created successfully!", "success")
            return redirect(url_for("view_invoice", invoice_id=res["invoice_id"]))
        else:
            flash(f"Failed to create invoice: {res.get('error')}", "danger")
            return redirect(url_for("calculator"))
    except Exception as e:
        logging.error(f"Error creating invoice: {e}")
        flash("An error occurred while generating the invoice.", "danger")
        return redirect(url_for("calculator"))


@app.route("/invoices")
def list_invoices():
    """Bill History & saved invoices management."""
    jeweller_id = session.get("jeweller", {}).get("id", "default")
    query = request.args.get("q", "")
    status_filter = request.args.get("status", "All")

    invoices = InvoiceService.list_invoices(jeweller_id=jeweller_id, query=query, status_filter=status_filter)
    stats = InvoiceService.get_invoice_stats(jeweller_id=jeweller_id)

    return render_template(
        "invoices.html",
        invoices=invoices,
        stats=stats,
        query=query,
        current_status=status_filter
    )


@app.route("/invoice/<invoice_id>")
def view_invoice(invoice_id):
    """Internal jeweller view of invoice with profit/margin metrics & share link."""
    jeweller_id = session.get("jeweller", {}).get("id", "default")
    invoice = InvoiceService.get_invoice_by_id(invoice_id, jeweller_id=jeweller_id)
    if not invoice:
        flash("Invoice not found.", "warning")
        return redirect(url_for("list_invoices"))

    jeweller = session.get("jeweller") or invoice.get("seller") or AuthService.get_jeweller_by_id(invoice.get("jeweller_id"))
    return render_template("invoice_view.html", invoice=invoice, jeweller=jeweller)


@app.route("/invoice/<invoice_id>/pdf")
def download_invoice_pdf(invoice_id):
    """Download GST Tax Invoice PDF for jeweller (supports customer vs internal store copy)."""
    try:
        jeweller_id = session.get("jeweller", {}).get("id", "default")
        invoice = InvoiceService.get_invoice_by_id(invoice_id, jeweller_id=jeweller_id)
        if not invoice:
            return "Invoice not found", 404

        mode = request.args.get("mode", "customer").lower()
        is_internal = (mode == "internal")
        jeweller = session.get("jeweller") or invoice.get("seller") or AuthService.get_jeweller_by_id(invoice.get("jeweller_id"))
        base_url = request.host_url
        pdf_bytes = InvoicePdfGenerator.generate_invoice_pdf(
            invoice,
            jeweller_profile=jeweller,
            base_url=base_url,
            is_internal=is_internal
        )

        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        suffix = "_StoreCopy" if is_internal else ""
        response.headers['Content-Disposition'] = f'inline; filename="Invoice_{invoice["invoice_number"]}{suffix}.pdf"'
        return response
    except Exception as e:
        logging.error(f"Error generating invoice PDF: {e}")
        return "PDF generation error", 500


@app.route("/invoice/share/<share_token>")
def share_invoice(share_token):
    """Public customer shareable link (confidential jeweller margins hidden)."""
    invoice = InvoiceService.get_invoice_by_share_token(share_token)
    if not invoice:
        flash("The requested invoice link is invalid or has expired.", "warning")
        return redirect(url_for("home_page"))

    jeweller = invoice.get("seller") or AuthService.get_jeweller_by_id(invoice.get("jeweller_id"))
    return render_template("invoice_share.html", invoice=invoice, jeweller=jeweller)


@app.route("/invoice/share/<share_token>/pdf")
def share_invoice_pdf(share_token):
    """Public customer PDF download stream."""
    try:
        invoice = InvoiceService.get_invoice_by_share_token(share_token)
        if not invoice:
            return "Invoice not found or link expired", 404

        base_url = request.host_url
        jeweller = invoice.get("seller") or AuthService.get_jeweller_by_id(invoice.get("jeweller_id"))
        pdf_bytes = InvoicePdfGenerator.generate_invoice_pdf(invoice, jeweller_profile=jeweller, base_url=base_url)

        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="Invoice_{invoice["invoice_number"]}.pdf"'
        return response
    except Exception as e:
        logging.error(f"Error generating shared invoice PDF: {e}")
        return "PDF generation error", 500


@app.route("/invoice/<invoice_id>/status", methods=["POST"])
def update_invoice_status_route(invoice_id):
    """Update invoice payment or issue status."""
    jeweller_id = session.get("jeweller", {}).get("id", "default")
    status = request.form.get("status", "Issued")
    InvoiceService.update_status(invoice_id, status, jeweller_id=jeweller_id)
    flash(f"Invoice status updated to '{status}'.", "info")
    return redirect(url_for("view_invoice", invoice_id=invoice_id))


@app.route("/invoice/<invoice_id>/delete", methods=["POST"])
def delete_invoice_route(invoice_id):
    """Delete invoice from database."""
    jeweller_id = session.get("jeweller", {}).get("id", "default")
    InvoiceService.delete_invoice(invoice_id, jeweller_id=jeweller_id)
    flash("Invoice removed from ledger.", "info")
    return redirect(url_for("list_invoices"))



# ============================================================
# 7. AI JEWELLER TRADE ADVISOR & PROPORTIONS
# ============================================================

@app.route("/assistant", methods=["GET", "POST"])
def assistant():
    """Interactive LLM-powered AI Trade Advisor with conversation memory & tools."""
    # Ensure stable session_id per client session
    session_id = session.get("chat_session_id")
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        session["chat_session_id"] = session_id

    response = None
    query = ""
    if request.method == "POST":
        query = request.form.get("query", "")
        if query:
            response = AIAssistantService.ask_assistant(query, session_id=session_id)

    chat_history = AITradeAdvisorAgent.get_conversation_history(session_id)
    ibja_rates = IBJAGoldService.get_current_rates()
    market_config = IndianMarketService.get_config()

    return render_template(
        "assistant.html",
        query=query,
        response=response,
        chat_history=chat_history,
        session_id=session_id,
        ibja_rates=ibja_rates,
        market_config=market_config,
        prop_data={},
        prop_eval=None
    )


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Live interactive chat API for ChatGPT-style real-time messaging."""
    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict()
        user_msg = (data.get("message") or data.get("query") or "").strip()
        if not user_msg:
            return jsonify({"success": False, "error": "Message cannot be empty."}), 400

        session_id = data.get("session_id") or session.get("chat_session_id")
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            session["chat_session_id"] = session_id

        context_diamond = data.get("context_diamond")

        res = AITradeAdvisorAgent.chat(
            user_message=user_msg,
            session_id=session_id,
            context_diamond=context_diamond
        )
        return jsonify(res)
    except Exception as e:
        logging.error(f"Error in api_chat: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/chat/history", methods=["GET"])
def api_chat_history():
    """Retrieves conversation history for current session."""
    session_id = request.args.get("session_id") or session.get("chat_session_id")
    if not session_id:
        return jsonify({"success": True, "history": []})
    history = AITradeAdvisorAgent.get_conversation_history(session_id)
    return jsonify({"success": True, "session_id": session_id, "history": history})


@app.route("/api/chat/reset", methods=["POST"])
def api_chat_reset():
    """Clears conversation memory for current session."""
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id") or session.get("chat_session_id")
    if session_id:
        AITradeAdvisorAgent.reset_session(session_id)
    return jsonify({"success": True, "message": "Conversation memory reset successfully."})


@app.route("/assistant/proportions", methods=["POST"])
def evaluate_proportions():
    session_id = session.get("chat_session_id")
    chat_history = AITradeAdvisorAgent.get_conversation_history(session_id) if session_id else []
    ibja_rates = IBJAGoldService.get_current_rates()
    market_config = IndianMarketService.get_config()

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
        chat_history=chat_history,
        session_id=session_id,
        ibja_rates=ibja_rates,
        market_config=market_config,
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
        provider = request.form.get("provider", "Bharat Diamond Bourse & Carat Hunter Wholesale")
        api_key = request.form.get("api_key", "").strip()
        igi_key = request.form.get("igi_api_key", "").strip()

        if igi_key:
            os.environ["IGI_API_KEY"] = igi_key

        IndianMarketService.save_config(usd_inr_rate=usd_inr, provider=provider, api_key=api_key)
        flash("Indian wholesale market settings updated.", "success")

    config = IndianMarketService.get_config()
    usd_inr = float(config.get("usd_inr_rate", 87.5))
    bullion_rates = IBJAGoldService.get_current_rates()
    daily_changes = bullion_rates.get("daily_changes", {})
    historical_prices = IBJAGoldService.get_historical_datewise_prices(days=30)
    chart_series = IBJAGoldService.get_chart_series(days=30)
    ch_matrix = CaratHunterService.get_wholesale_index_matrix(usd_inr_rate=usd_inr)
    ch_overview = CaratHunterService.get_market_overview()

    return render_template(
        "market_rates.html",
        config=config,
        bullion_rates=bullion_rates,
        daily_changes=daily_changes,
        historical_prices=historical_prices,
        chart_series=chart_series,
        ch_matrix=ch_matrix,
        ch_overview=ch_overview
    )


@app.route("/api/market-rates/live")
def api_market_rates_live():
    """Live streaming endpoint for stock-market ticker, cards, and Chart.js series."""
    force = request.args.get("force", "false").lower() in ("true", "1", "yes")
    config = IndianMarketService.get_config()
    usd_inr = float(config.get("usd_inr_rate", 87.5))
    bullion_rates = IBJAGoldService.get_current_rates(force_refresh=force)
    chart_series = IBJAGoldService.get_chart_series(days=30)
    ch_overview = CaratHunterService.get_market_overview()
    
    # 1ct benchmark quotes
    nat_1ct = CaratHunterService.get_price_check(1.0, "F", "VS1", "round", "natural", usd_inr_rate=usd_inr)
    lab_1ct = CaratHunterService.get_price_check(1.0, "F", "VS1", "round", "lab-grown", usd_inr_rate=usd_inr)

    return jsonify({
        "success": True,
        "is_live": bullion_rates.get("is_live", True),
        "rates": bullion_rates.get("rates", {}),
        "daily_changes": bullion_rates.get("daily_changes", {}),
        "chart_series": chart_series,
        "carathunter": {
            "natural_1ct": nat_1ct,
            "lab_1ct": lab_1ct,
            "overview": ch_overview
        },
        "session": bullion_rates.get("session", "Live Session"),
        "timestamp": bullion_rates.get("fetched_timestamp", "")
    })


@app.route("/api/carathunter/quote")
def api_carathunter_quote():
    """Live CaratHunter price_check API for any carat, color, clarity, shape, origin."""
    try:
        carat = float(request.args.get("carat", 1.0))
        color = request.args.get("color", "F")
        clarity = request.args.get("clarity", "VS1")
        shape = request.args.get("shape", "round")
        origin = request.args.get("origin", "natural")
        config = IndianMarketService.get_config()
        usd_inr = float(config.get("usd_inr_rate", 87.5))

        quote = CaratHunterService.get_price_check(
            carat=carat,
            color=color,
            clarity=clarity,
            shape=shape,
            origin=origin,
            usd_inr_rate=usd_inr
        )
        return jsonify({"success": True, "data": quote})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/carathunter/certificate")
def api_carathunter_cert():
    """Live certificate lookup (IGI, GIA) against CaratHunter's 24.5M diamonds."""
    cert_num = request.args.get("certificate_number", "").strip()
    if not cert_num:
        return jsonify({"success": False, "error": "Missing certificate_number"}), 400
    res = CaratHunterService.lookup_certificate(cert_num)
    return jsonify({"success": True, "data": res})


@app.route("/api/inventory/revalue", methods=["POST"])
def api_inventory_revalue():
    """Triggers live market revaluation of inventory portfolio using CaratHunter quotes."""
    try:
        jeweller_id = session.get("jeweller", {}).get("id", "default")
        result = InventoryService.revalue_all_inventory(jeweller_id=jeweller_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




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
            # Trigger mandatory Bullions.co.in live fetch on jeweller login
            synced_rates = IBJAGoldService.sync_on_login(force_refresh=True)
            status_badge = "LIVE" if synced_rates.get("is_live") else "STALE"
            gold_24k_str = synced_rates.get("rates", {}).get("24K", {}).get("formatted_rate_per_gram", "₹ 14,828/g")
            silver_999_str = synced_rates.get("rates", {}).get("Silver_999", {}).get("formatted_rate_per_gram", "₹ 212/g")
            flash(
                f"Welcome back, {jeweller['owner_name']} ({jeweller['business_name']})! "
                f"Bullions.co.in rates synced [{status_badge}]: Gold 24K: {gold_24k_str} • Silver 999: {silver_999_str}.",
                "success"
            )
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
        IBJAGoldService.sync_on_login(force_refresh=True)
        flash("Jeweller account registered successfully! Latest Bullion rates synchronized.", "success")
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