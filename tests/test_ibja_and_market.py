import pytest
from decimal import Decimal
from DiamondPricePrediction.services.ibja_gold_service import IBJAGoldService
from DiamondPricePrediction.services.licensed_diamond_service import LicensedDiamondService
from DiamondPricePrediction.services.indian_market_service import IndianMarketService
from DiamondPricePrediction.services.valuation_engine import ValuationEngine

def test_ibja_gold_rates_purity_factors():
    """Verify IBJA gold rates calculation across purities with Decimal precision."""
    rates_data = IBJAGoldService.get_current_rates()

    assert "rates" in rates_data
    assert "24K" in rates_data["rates"]
    assert "22K" in rates_data["rates"]
    assert "18K" in rates_data["rates"]
    assert "14K" in rates_data["rates"]
    assert "Silver_999" in rates_data["rates"]

    base_24k = rates_data["base_24k_rate_per_gram"]
    assert base_24k >= 5000.0

    rate_24k = rates_data["rates"]["24K"]["rate_per_gram"]
    rate_22k = rates_data["rates"]["22K"]["rate_per_gram"]
    rate_18k = rates_data["rates"]["18K"]["rate_per_gram"]

    # 22K should be exactly 22/24 of 24K
    expected_22k = round(base_24k * (22.0 / 24.0), 2)
    assert abs(rate_22k - expected_22k) <= 0.05

    # 18K should be exactly 75% of 24K
    expected_18k = round(base_24k * 0.75, 2)
    assert abs(rate_18k - expected_18k) <= 0.05

    # Check timestamps and metadata
    assert len(rates_data["publication_timestamp"]) > 5
    assert len(rates_data["fetched_timestamp"]) > 5
    assert "IBJA" in rates_data["source"]
    assert rates_data["freshness"] is not None

def test_ibja_metal_cost_formula():
    """Verify net weight, wastage % and purity rate calculation."""
    res = IBJAGoldService.calculate_metal_cost(
        net_weight_grams=10.0,
        purity="22K",
        wastage_pct=6.0,
        custom_base_rate_24k=8000.0
    )
    # 22K rate = 8000 * (22/24) = 7333.33
    assert res["rate_per_gram"] == 7333.33
    # 10g net + 6% wastage = 10.6g gross
    assert res["gross_weight_grams"] == 10.6
    # 10.6 * 7333.33 = 77733.30
    assert res["total_metal_cost"] == 77733.30

def test_licensed_diamond_pricing_and_surat_lgd():
    """Verify natural diamond BDB benchmark and Surat SDB lab-grown manufacturing pricing."""
    # Natural 1.50 ct D VVS1 Ideal
    spec_nat = {
        "carat": 1.50,
        "color": "D",
        "clarity": "VVS1",
        "cut": "Ideal",
        "shape": "Round Brilliant",
        "origin_type": "Natural"
    }
    q_nat = LicensedDiamondService.get_pricing_quote(spec_nat)
    assert q_nat["data_available"] is True
    assert q_nat["origin_type"] == "Natural"
    assert "Bharat Diamond Bourse" in q_nat["source"] or "RapNet" in q_nat["source"]
    assert q_nat["total_wholesale_inr"] > 500000

    # Lab-Grown 1.50 ct D VVS1 Ideal (Surat CVD/HPHT Hub)
    spec_lg = {
        "carat": 1.50,
        "color": "D",
        "clarity": "VVS1",
        "cut": "Ideal",
        "shape": "Round Brilliant",
        "origin_type": "Lab-Grown",
        "growth_process": "CVD"
    }
    q_lg = LicensedDiamondService.get_pricing_quote(spec_lg)
    assert q_lg["data_available"] is True
    assert q_lg["origin_type"] == "Lab-Grown"
    assert "Surat Diamond Bourse" in q_lg["source"]
    # Lab grown price should be in typical wholesale range (< 60,000 for 1.5ct)
    assert q_lg["total_wholesale_inr"] < 60000
    assert q_lg["price_per_carat_inr"] < 40000

def test_igi_verification_separation_notice():
    """Verify that valuation engine includes explicit IGI separation notice."""
    spec = {
        "report_number": "584392810",
        "origin_type": "Natural",
        "carat": 1.0,
        "color": "F",
        "clarity": "VS1",
        "cut": "Ideal"
    }
    market_quote = IndianMarketService.get_indian_wholesale_quote(spec)
    val = ValuationEngine.calculate_valuation(
        diamond_spec=spec,
        ml_prediction_usd=4500.0,
        comps_data={},
        market_quote_inr=market_quote
    )

    assert "igi_separation_notice" in val
    assert "independent" in val["igi_separation_notice"].lower()
    assert "grading" in val["igi_separation_notice"].lower()
    assert "not perform monetary appraisals" in val["igi_separation_notice"].lower() or "not issue commercial appraisals" in val["igi_separation_notice"].lower() or "does not perform monetary appraisals" in val["igi_separation_notice"].lower()
