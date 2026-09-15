import pytest
from DiamondPricePrediction.services.indian_market_service import IndianMarketService
from DiamondPricePrediction.services.valuation_engine import ValuationEngine
from DiamondPricePrediction.services.comparables_service import ComparablesService

def test_indian_market_quote_natural_vs_lab():
    # Natural 1.02 ct E VVS1
    spec_nat = {
        "report_number": "584392810",
        "origin_type": "Natural",
        "carat": 1.02,
        "color": "E",
        "clarity": "VVS1",
        "cut": "Ideal",
        "shape": "Round Brilliant",
        "fluorescence": "None"
    }
    quote_nat = IndianMarketService.get_indian_wholesale_quote(spec_nat)
    assert quote_nat["currency"] == "INR"
    assert quote_nat["total_wholesale_inr"] > 300000
    assert "Mumbai Bharat Diamond Bourse" in quote_nat["source"]

    # Lab-Grown 2.04 ct D VVS2
    spec_lg = {
        "report_number": "LG612345678",
        "origin_type": "Lab-Grown",
        "growth_process": "CVD",
        "carat": 2.04,
        "color": "D",
        "clarity": "VVS2",
        "cut": "Ideal",
        "shape": "Round Brilliant",
        "fluorescence": "None"
    }
    quote_lg = IndianMarketService.get_indian_wholesale_quote(spec_lg)
    assert quote_lg["currency"] == "INR"
    assert quote_lg["total_wholesale_inr"] < 150000
    assert quote_lg["price_per_carat_inr"] < 60000
    assert "Surat Diamond Bourse" in quote_lg["source"]

def test_valuation_engine_deal_calculations():
    spec = {
        "report_number": "584392810",
        "origin_type": "Natural",
        "carat": 1.02,
        "color": "E",
        "clarity": "VVS1",
        "cut": "Ideal",
        "shape": "Round Brilliant",
        "depth": 61.8,
        "table": 56.5
    }
    market_quote = IndianMarketService.get_indian_wholesale_quote(spec)
    comps = ComparablesService.find_comparables(spec["carat"], spec["cut"], spec["color"], spec["clarity"])
    
    val = ValuationEngine.calculate_valuation(
        diamond_spec=spec,
        ml_prediction_usd=5500.0,
        comps_data=comps,
        market_quote_inr=market_quote,
        asking_price_inr=380000
    )

    assert val["status"] == "Valuation Computed"
    assert val["data_available"] is True
    assert val["today_market_price"] > 0
    assert val["today_market_price_formatted"].startswith("₹")
    assert val["fair_market_value"] > 0
    assert val["suggested_buy_price"] < val["fair_market_value"]
    assert val["suggested_sell_price"] > val["fair_market_value"]
    assert val["expected_profit"] > 0
    assert val["expected_margin_pct"] > 0
    assert val["gst_amount"] == round(val["suggested_sell_price"] * 0.03)
    assert val["confidence_score"] >= 70
    assert "Bharat Diamond Bourse" in val["source"] or "SDB" in val["source"]
    assert len(val["why_this_price"]) > 30

def test_invalid_spec_data_availability():
    invalid_spec = {"carat": -1.0}
    quote = IndianMarketService.get_indian_wholesale_quote(invalid_spec)
    assert quote["data_available"] is False

    val = ValuationEngine.calculate_valuation(
        diamond_spec=invalid_spec,
        ml_prediction_usd=0,
        comps_data={},
        market_quote_inr=quote
    )
    assert val["data_available"] is False
    assert val["status"] == "Live Market Pricing Unavailable"

def test_indian_rupee_formatting():
    assert IndianMarketService.format_inr(125000) == "₹ 1,25,000"
    assert IndianMarketService.format_inr(4500000) == "₹ 45,00,000"
    assert IndianMarketService.format_inr_lakhs(450000) == "₹ 4.50 Lakh"
    assert IndianMarketService.format_inr_lakhs(12500000) == "₹ 1.25 Cr"

def test_ai_deal_advisor_verdicts():
    spec = {
        "report_number": "584392810",
        "origin_type": "Natural",
        "carat": 1.02,
        "color": "E",
        "clarity": "VVS1",
        "cut": "Ideal",
        "shape": "Round Brilliant",
        "depth": 61.8,
        "table": 56.5
    }
    market_quote = IndianMarketService.get_indian_wholesale_quote(spec)
    comps = ComparablesService.find_comparables(spec["carat"], spec["cut"], spec["color"], spec["clarity"])
    
    # 1. Asking price at Max Buy Price -> Verdict BUY
    val_buy = ValuationEngine.calculate_valuation(
        diamond_spec=spec,
        ml_prediction_usd=5500.0,
        comps_data=comps,
        market_quote_inr=market_quote,
        asking_price_inr=300000
    )
    deal_buy = val_buy["deal_advisor"]
    assert deal_buy["fair_value"] > 0
    assert deal_buy["max_buy_price"] > 0
    assert deal_buy["expected_profit"] > 0
    assert deal_buy["deal_score"] >= 70
    assert deal_buy["verdict"] == "BUY"
    assert deal_buy["badge_class"] == "badge-emerald"

    # 2. Asking price above Fair Value -> Verdict NEGOTIATE
    val_neg = ValuationEngine.calculate_valuation(
        diamond_spec=spec,
        ml_prediction_usd=5500.0,
        comps_data=comps,
        market_quote_inr=market_quote,
        asking_price_inr=val_buy["fair_market_value"] + 20000
    )
    deal_neg = val_neg["deal_advisor"]
    assert deal_neg["verdict"] == "NEGOTIATE"
    assert deal_neg["badge_class"] == "badge-warning"
    assert 40 <= deal_neg["deal_score"] <= 69

    # 3. Asking price way above high bound -> Verdict WALK AWAY
    val_walk = ValuationEngine.calculate_valuation(
        diamond_spec=spec,
        ml_prediction_usd=5500.0,
        comps_data=comps,
        market_quote_inr=market_quote,
        asking_price_inr=val_buy["high_estimate"] + 200000
    )
    deal_walk = val_walk["deal_advisor"]
    assert deal_walk["verdict"] == "WALK AWAY"
    assert deal_walk["badge_class"] == "badge-danger"
    assert deal_walk["deal_score"] < 40


