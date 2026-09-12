import os
import sys
import pytest

from DiamondPricePrediction.services.gia_service import GIAService
from DiamondPricePrediction.services.market_data_service import MarketDataService
from DiamondPricePrediction.services.comparables_service import ComparablesService
from DiamondPricePrediction.services.valuation_engine import ValuationEngine
from DiamondPricePrediction.services.inventory_service import InventoryService
from DiamondPricePrediction.services.ai_assistant_service import AIAssistantService
from DiamondPricePrediction.pipeline.prediction import Customdata, PredictionPipeline
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_gia_parsing_and_verification():
    sample_text = """
    GIA NATURAL DIAMOND DOSSIER
    GIA Report Number: 2458921840
    Shape and Cutting Style: Round Brilliant
    Measurements: 6.45 - 6.48 x 3.99 mm
    Carat Weight: 1.01 carat
    Color Grade: E
    Clarity Grade: VVS1
    Cut Grade: Excellent
    Polish: Excellent
    Symmetry: Excellent
    Fluorescence: None
    Depth: 61.7 %
    Table: 57.0 %
    """
    parsed = GIAService.parse_raw_text(sample_text)
    norm = parsed["normalized"]
    assert norm["report_number"] == "2458921840"
    assert norm["carat"] == 1.01
    assert norm["color"] == "E"
    assert norm["clarity"] == "VVS1"
    assert norm["cut"] == "Ideal"
    assert norm["depth"] == 61.7
    assert norm["table"] == 57.0
    assert norm["x"] == 6.45
    assert norm["y"] == 6.48
    assert norm["z"] == 3.99

    verif = GIAService.get_verification_info("2458921840")
    assert "report-check?reportno=2458921840" in verif["report_check_url"]
    assert verif["report_number"] == "2458921840"


def test_market_data_service_real_data_policy():
    MarketDataService.save_config("None", "")
    config = MarketDataService.get_config()
    assert config["api_key_configured"] is False

    quote = MarketDataService.fetch_live_market_quote({"carat": 1.0})
    assert quote["is_connected"] is False
    assert quote["live_quote"] is None
    assert "Not Connected" in quote["status_label"]


def test_comparables_service_benchmark_query():
    comps = ComparablesService.find_comparables(
        carat=1.01,
        cut="Ideal",
        color="E",
        clarity="VVS1",
        depth=61.7,
        table=57.0,
        max_results=5
    )
    assert comps["insufficient_data"] is False
    assert comps["sample_count"] > 0
    assert len(comps["comparables"]) > 0
    first_comp = comps["comparables"][0]
    assert "carat" in first_comp
    assert "price" in first_comp
    assert "similarity_score" in first_comp
    assert first_comp["similarity_score"] >= 50.0


def test_valuation_engine_and_jeweller_deal():
    diamond_spec = {
        "report_number": "2458921840",
        "origin_type": "Natural",
        "shape": "Round Brilliant",
        "carat": 1.01,
        "cut": "Ideal",
        "color": "E",
        "clarity": "VVS1",
        "depth": 61.7,
        "table": 57.0,
        "x": 6.45,
        "y": 6.48,
        "z": 3.99
    }
    comps = ComparablesService.find_comparables(1.01, "Ideal", "E", "VVS1", 61.7, 57.0)
    market_quote = MarketDataService.fetch_live_market_quote(diamond_spec)
    
    val = ValuationEngine.calculate_valuation(
        diamond_spec=diamond_spec,
        ml_prediction=7200.0,
        comps_data=comps,
        market_quote_data=market_quote,
        asking_price=6500.0
    )

    assert val["insufficient_data"] is False
    assert val["midpoint_value"] > 0
    assert val["price_per_carat"] > 0
    assert val["confidence_score"] >= 50
    assert val["jeweller_deal"] is not None
    assert val["jeweller_deal"]["asking_price"] == 6500.0
    assert "recommended_retail" in val["jeweller_deal"]


def test_inventory_service_crud():
    InventoryService.init_db()
    spec = {"report_number": "TEST99999", "carat": 1.25, "cut": "Ideal", "color": "D", "clarity": "VVS1", "shape": "Round Brilliant", "origin_type": "Natural", "depth": 61.5, "table": 57.0, "x": 6.9, "y": 6.92, "z": 4.25}
    val = {"midpoint_value": 9500.0, "low_estimate": 8700.0, "high_estimate": 10200.0, "confidence_score": 92}
    
    item_id = InventoryService.save_diamond(spec, val, asking_price=8800.0, status="In Stock", tag="Inventory")
    assert len(item_id) > 0

    item = InventoryService.get_diamond_by_id(item_id)
    assert item is not None
    assert item["report_number"] == "TEST99999"
    assert item["carat"] == 1.25

    inv_list = InventoryService.get_inventory()
    assert any(x["id"] == item_id for x in inv_list)

    deleted = InventoryService.delete_diamond(item_id)
    assert deleted is True


def test_ai_assistant_service():
    eval_res = AIAssistantService.evaluate_proportions("Round Brilliant", table=56.0, depth=61.8, x=6.45, y=6.48, z=3.99)
    assert eval_res["overall_proportion_score"] >= 90

    ans = AIAssistantService.ask_assistant("magic sizes")
    assert "Magic Carat Sizes" in ans["answer"]


def test_flask_endpoints(client):
    # GET routes
    assert client.get("/").status_code == 200
    assert client.get("/predict").status_code == 200
    assert client.get("/predict?sample=2458921840").status_code == 200
    assert client.get("/inventory").status_code == 200
    assert client.get("/compare").status_code == 200
    assert client.get("/market-settings").status_code == 200
    assert client.get("/assistant").status_code == 200

    # POST /predict
    post_data = {
        "report_number": "2458921840",
        "origin_type": "Natural",
        "shape": "Round Brilliant",
        "carat": "1.01",
        "cut": "Ideal",
        "color": "E",
        "clarity": "VVS1",
        "depth": "61.7",
        "table": "57.0",
        "x": "6.45",
        "y": "6.48",
        "z": "3.99",
        "asking_price": "6500"
    }
    res = client.post("/predict", data=post_data)
    assert res.status_code == 200
    assert b"VALUATION &amp; VERIFICATION DOSSIER" in res.data or b"VALUATION & VERIFICATION DOSSIER" in res.data
