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
    assert val["fair_market_value"] > 0
    assert val["suggested_buy_price"] < val["fair_market_value"]
    assert val["suggested_sell_price"] > val["fair_market_value"]
    assert val["expected_profit"] > 0
    assert val["expected_margin_pct"] > 0
    assert val["gst_amount"] == round(val["suggested_sell_price"] * 0.03)
    assert val["confidence_score"] >= 70
    assert len(val["why_this_price"]) > 30

def test_indian_rupee_formatting():
    assert IndianMarketService.format_inr(125000) == "₹ 1,25,000"
    assert IndianMarketService.format_inr(4500000) == "₹ 45,00,000"
    assert IndianMarketService.format_inr_lakhs(450000) == "₹ 4.50 Lakh"
    assert IndianMarketService.format_inr_lakhs(12500000) == "₹ 1.25 Cr"
