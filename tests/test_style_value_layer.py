import pytest
from DiamondPricePrediction.services.style_value_service import StyleValueService
from DiamondPricePrediction.services.valuation_engine import ValuationEngine
from app import app

def test_style_value_service_classification():
    # Premium spec
    premium_spec = {
        "carat": 1.02,
        "color": "E",
        "clarity": "VVS1",
        "cut": "Ideal",
        "polish": "Excellent",
        "symmetry": "Excellent",
        "fluorescence": "None",
        "table": 56.5,
        "depth": 61.8
    }
    res_premium = StyleValueService.evaluate_ai_face_layer(premium_spec)
    assert res_premium["ai_face_tier"] == "premium"
    assert res_premium["face_score"] >= 82
    assert "Premium" in res_premium["ai_face_label"]

    # Value-oriented spec
    value_spec = {
        "carat": 0.90,
        "color": "I",
        "clarity": "SI2",
        "cut": "Good",
        "polish": "Good",
        "symmetry": "Good",
        "fluorescence": "Strong Blue",
        "table": 63.0,
        "depth": 65.0
    }
    res_value = StyleValueService.evaluate_ai_face_layer(value_spec)
    assert res_value["ai_face_tier"] == "value-oriented"
    assert res_value["face_score"] < 62


def test_valuation_engine_pricing_signals():
    spec = {
        "report_number": "584392810",
        "carat": 1.00,
        "color": "F",
        "clarity": "VS1",
        "cut": "Ideal",
        "depth": 61.8,
        "table": 57.0,
        "x": 6.46,
        "y": 6.49,
        "z": 4.00,
        "origin_type": "Natural"
    }
    quote = {"total_wholesale_inr": 440000, "data_available": True}
    comps = {"sample_count": 10, "statistics": {"median_price_inr": 440000, "p25_price_inr": 400000, "p75_price_inr": 480000}}

    # Default moderate signal
    val_mod = ValuationEngine.calculate_valuation(
        diamond_spec=spec,
        ml_prediction_usd=5000.0,
        comps_data=comps,
        market_quote_inr=quote,
        pricing_preference="moderate"
    )

    # Premium signal
    val_prem = ValuationEngine.calculate_valuation(
        diamond_spec=spec,
        ml_prediction_usd=5000.0,
        comps_data=comps,
        market_quote_inr=quote,
        pricing_preference="premium"
    )

    # Value-oriented signal
    val_val = ValuationEngine.calculate_valuation(
        diamond_spec=spec,
        ml_prediction_usd=5000.0,
        comps_data=comps,
        market_quote_inr=quote,
        pricing_preference="value-oriented"
    )

    assert val_prem["suggested_sell_price"] > val_mod["suggested_sell_price"]
    assert val_mod["suggested_sell_price"] > val_val["suggested_sell_price"]
    assert val_prem["active_markup_pct"] == 38.0
    assert val_val["active_markup_pct"] == 14.0
    assert "style_value_analysis" in val_prem
    assert "confidence_score" in val_prem


def test_appraise_route_with_pricing_signal():
    client = app.test_client()
    resp = client.get("/appraise?report_number=584392810&pricing_preference=premium")
    assert resp.status_code == 200
    assert b"AI Face / Style-Value Layer" in resp.data
    assert b"Premium Luxury" in resp.data
