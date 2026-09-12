import os
import sys
import json
from datetime import datetime, timezone
from flask import Flask, request, render_template, redirect, url_for, flash

from DiamondPricePrediction.utils.logger import logging
from DiamondPricePrediction.utils.exception import CustomException
from DiamondPricePrediction.pipeline.prediction import Customdata, PredictionPipeline
from DiamondPricePrediction.services.gia_service import GIAService
from DiamondPricePrediction.services.market_data_service import MarketDataService
from DiamondPricePrediction.services.comparables_service import ComparablesService
from DiamondPricePrediction.services.valuation_engine import ValuationEngine
from DiamondPricePrediction.services.inventory_service import InventoryService
from DiamondPricePrediction.services.ai_assistant_service import AIAssistantService

# ============================================================
# FLASK APPLICATION INITIALIZATION
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "gemforecast-ai-secret-key-2026")

# Initialize SQLite database schema
InventoryService.init_db()

# Pre-load ML pipeline
prediction_pipeline = PredictionPipeline()


# ============================================================
# 1. PLATFORM HOME / LANDING PAGE
# ============================================================

@app.route("/")
def home_page():
    market_status = MarketDataService.get_config()
    workspace_stats = InventoryService.get_summary_stats()
    return render_template(
        "index.html",
        market_status=market_status,
        workspace_stats=workspace_stats
    )


# ============================================================
# 2. DIAMOND VALUATION & GIA APPRAISAL PORTAL
# ============================================================

@app.route("/predict", methods=["GET", "POST"])
def predict():
    market_config = MarketDataService.get_config()

    # --------------------------------------------------------
    # GET: Render Appraisal Form
    # --------------------------------------------------------
    if request.method == "GET":
        sample_key = request.args.get("sample")
        sample_cert = None
        form_data = {}

        if sample_key:
            sample_cert = GIAService.get_sample_report(sample_key)
            if sample_cert:
                form_data = sample_cert

        return render_template(
            "form.html",
            form_data=form_data,
            sample_cert=sample_cert,
            market_config=market_config
        )

    # --------------------------------------------------------
    # POST: Process Full Valuation & Verification Dossier
    # --------------------------------------------------------
    try:
        # 1. Ingest Raw Input Form Fields
        report_num = request.form.get("report_number", "").strip() or None
        origin_type = request.form.get("origin_type", "Natural")
        shape = request.form.get("shape", "Round Brilliant")

        carat = float(request.form.get("carat", 1.0))
        depth = float(request.form.get("depth", 61.7))
        table = float(request.form.get("table", 57.0))
        x = float(request.form.get("x", 6.45))
        y = float(request.form.get("y", 6.48))
        z = float(request.form.get("z", 3.99))

        cut = request.form.get("cut", "Ideal")
        color = request.form.get("color", "E").upper()
        clarity = request.form.get("clarity", "VS1").upper()

        polish = request.form.get("polish", "Excellent")
        symmetry = request.form.get("symmetry", "Excellent")
        fluorescence = request.form.get("fluorescence", "None")

        asking_price_raw = request.form.get("asking_price")
        asking_price = float(asking_price_raw) if asking_price_raw and asking_price_raw.strip() else None

        diamond_spec = {
            "report_number": report_num,
            "origin_type": origin_type,
            "shape": shape,
            "carat": carat,
            "cut": cut,
            "color": color,
            "clarity": clarity,
            "depth": depth,
            "table": table,
            "x": x,
            "y": y,
            "z": z,
            "polish": polish,
            "symmetry": symmetry,
            "fluorescence": fluorescence,
            "asking_price": asking_price
        }

        # 2. GIA Verification Workflow (Official Portal / API)
        gia_verification = GIAService.get_verification_info(report_num)

        # 3. Wholesale Market Provider Query (Real status / Connected API)
        market_quote = MarketDataService.fetch_live_market_quote(diamond_spec)

        # 4. Query 193.5k Real Benchmark Database Comparables
        comps_data = ComparablesService.find_comparables(
            carat=carat,
            cut=cut,
            color=color,
            clarity=clarity,
            depth=depth,
            table=table,
            max_results=8
        )

        # 5. Historical ML Model Valuation & SHAP Attribution
        custom_data_obj = Customdata(
            carat=carat,
            depth=depth,
            table=table,
            x=x,
            y=y,
            z=z,
            cut=cut,
            color=color,
            clarity=clarity,
            origin_type=origin_type,
            report_number=report_num
        )
        features_df = custom_data_obj.get_data_as_dataframe()

        ml_pred_arr = prediction_pipeline.prediction(features_df)
        raw_ml_prediction = float(ml_pred_arr[0])

        shap_explanation = prediction_pipeline.explain_prediction(features_df)

        # 6. Composite Valuation & Jeweller Deal Synthesis
        valuation = ValuationEngine.calculate_valuation(
            diamond_spec=diamond_spec,
            ml_prediction=raw_ml_prediction,
            comps_data=comps_data,
            market_quote_data=market_quote,
            asking_price=asking_price
        )

        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        return render_template(
            "result.html",
            diamond_spec=diamond_spec,
            diamond_spec_json=json.dumps(diamond_spec),
            valuation=valuation,
            valuation_json=json.dumps(valuation),
            gia_verification=gia_verification,
            comparables=comps_data,
            shap_explanation=shap_explanation,
            timestamp=timestamp_str
        )

    except Exception as e:
        logging.error(f"Error occurred during diamond valuation pipeline: {e}")
        raise CustomException(e, sys)


# ============================================================
# 3. GIA CERTIFICATE PDF PARSER ROUTE
# ============================================================

@app.route("/parse-gia-pdf", methods=["POST"])
def parse_gia_pdf():
    try:
        if "gia_pdf" not in request.files:
            return render_template("form.html", upload_error="No PDF file uploaded.", form_data={})

        file = request.files["gia_pdf"]
        if file.filename == "":
            return render_template("form.html", upload_error="No file selected.", form_data={})

        pdf_bytes = file.read()
        parsed_result = GIAService.extract_from_pdf(pdf_bytes)

        if "error" in parsed_result:
            return render_template("form.html", upload_error=parsed_result["error"], form_data={})

        form_data = parsed_result.get("normalized", {})
        logging.info(f"GIA PDF parsed successfully: {form_data}")

        return render_template(
            "form.html",
            form_data=form_data,
            upload_success="GIA Certificate fields extracted successfully from PDF."
        )

    except Exception as e:
        logging.error(f"Failed to process GIA PDF: {e}")
        return render_template("form.html", upload_error=f"PDF parsing error: {str(e)}", form_data={})


# ============================================================
# 4. JEWELLER WORKSPACE & INVENTORY
# ============================================================

@app.route("/inventory")
def inventory():
    tag_filter = request.args.get("tag", "All")
    items = InventoryService.get_inventory(tag_filter=tag_filter)
    stats = InventoryService.get_summary_stats()
    return render_template("inventory.html", items=items, stats=stats, current_tag=tag_filter)


@app.route("/inventory/save", methods=["POST"])
def save_to_inventory():
    try:
        spec_json = request.form.get("diamond_spec_json", "{}")
        val_json = request.form.get("valuation_json", "{}")
        tag = request.form.get("tag", "Inventory")
        asking_price = request.form.get("asking_price")

        diamond_spec = json.loads(spec_json)
        valuation = json.loads(val_json)
        ask_val = float(asking_price) if asking_price and asking_price != "None" else None

        item_id = InventoryService.save_diamond(
            diamond_spec=diamond_spec,
            valuation_result=valuation,
            asking_price=ask_val,
            status="In Stock" if tag == "Inventory" else tag,
            tag=tag
        )
        return redirect(url_for("inventory"))
    except Exception as e:
        logging.error(f"Error saving to inventory: {e}")
        return redirect(url_for("inventory"))


@app.route("/inventory/view/<item_id>")
def view_inventory_item(item_id):
    item = InventoryService.get_diamond_by_id(item_id)
    if not item or not item.get("dossier"):
        return redirect(url_for("inventory"))

    dossier = item["dossier"]
    diamond_spec = dossier["diamond_spec"]
    valuation = dossier["valuation"]

    gia_verification = GIAService.get_verification_info(diamond_spec.get("report_number"))
    comps_data = ComparablesService.find_comparables(
        carat=diamond_spec.get("carat", 1.0),
        cut=diamond_spec.get("cut", "Ideal"),
        color=diamond_spec.get("color", "E"),
        clarity=diamond_spec.get("clarity", "VS1"),
        depth=diamond_spec.get("depth", 61.7),
        table=diamond_spec.get("table", 57.0)
    )

    custom_data = Customdata(
        carat=diamond_spec.get("carat", 1.0),
        depth=diamond_spec.get("depth", 61.7),
        table=diamond_spec.get("table", 57.0),
        x=diamond_spec.get("x", 6.45),
        y=diamond_spec.get("y", 6.48),
        z=diamond_spec.get("z", 3.99),
        cut=diamond_spec.get("cut", "Ideal"),
        color=diamond_spec.get("color", "E"),
        clarity=diamond_spec.get("clarity", "VS1")
    )
    shap_explanation = prediction_pipeline.explain_prediction(custom_data.get_data_as_dataframe())
    timestamp_str = item.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))

    return render_template(
        "result.html",
        diamond_spec=diamond_spec,
        diamond_spec_json=json.dumps(diamond_spec),
        valuation=valuation,
        valuation_json=json.dumps(valuation),
        gia_verification=gia_verification,
        comparables=comps_data,
        shap_explanation=shap_explanation,
        timestamp=timestamp_str
    )


@app.route("/inventory/delete/<item_id>", methods=["POST"])
def delete_inventory_item(item_id):
    InventoryService.delete_diamond(item_id)
    return redirect(url_for("inventory"))


# ============================================================
# 5. MULTI-DIAMOND COMPARISON MATRIX
# ============================================================

@app.route("/compare")
def compare():
    items = InventoryService.get_inventory()
    if len(items) >= 2:
        compare_diamonds = items[:4]
    else:
        # Pre-populate with sample diamonds for comparison demo
        samples = [
            GIAService.get_sample_report("2458921840"),
            GIAService.get_sample_report("5221789034"),
            GIAService.get_sample_report("6439012345")
        ]
        compare_diamonds = []
        for s in samples:
            if s:
                custom_d = Customdata(
                    carat=s["carat"], depth=s["depth_pct"], table=s["table_pct"],
                    x=s["x"], y=s["y"], z=s["z"], cut=s["cut"], color=s["color"], clarity=s["clarity"]
                )
                pred = float(prediction_pipeline.prediction(custom_d.get_data_as_dataframe())[0])
                comps = ComparablesService.find_comparables(s["carat"], s["cut"], s["color"], s["clarity"])
                val = ValuationEngine.calculate_valuation(s, pred, comps, {"is_connected": False, "live_quote": None, "source": "Unconnected"}, s.get("asking_price"))
                s["valuation_midpoint"] = val.get("midpoint_value")
                s["confidence_score"] = val.get("confidence_score")
                compare_diamonds.append(s)

    return render_template("compare.html", diamonds=compare_diamonds)


# ============================================================
# 6. MARKET & GIA API CONFIGURATION
# ============================================================

@app.route("/market-settings", methods=["GET", "POST"])
def market_settings():
    msg = None
    if request.method == "POST":
        provider = request.form.get("provider", "None")
        api_key = request.form.get("api_key", "").strip()
        base_url = request.form.get("base_url", "").strip()
        gia_key = request.form.get("gia_api_key", "").strip()

        if gia_key:
            os.environ["GIA_API_KEY"] = gia_key

        MarketDataService.save_config(provider=provider, api_key=api_key, base_url=base_url)
        msg = "Configuration saved successfully. Wholesale feed status updated."

    config = MarketDataService.get_config()
    return render_template("market_settings.html", config=config, message=msg)


# ============================================================
# 7. GEMOLOGICAL AI ASSISTANT & PROPORTIONS
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
    table = float(request.form.get("table", 57.0))
    depth = float(request.form.get("depth", 61.7))
    x = float(request.form.get("x", 6.45))
    y = float(request.form.get("y", 6.48))
    z = float(request.form.get("z", 3.99))

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
# RUN FLASK APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8080
    )