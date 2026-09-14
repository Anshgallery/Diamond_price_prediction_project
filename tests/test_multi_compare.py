import pytest
from DiamondPricePrediction.services.igi_service import IGIService
from DiamondPricePrediction.services.indian_market_service import IndianMarketService
from DiamondPricePrediction.services.valuation_engine import ValuationEngine
from DiamondPricePrediction.services.comparables_service import ComparablesService
from DiamondPricePrediction.services.ai_assistant_service import AIAssistantService

def test_5_report_comparison_and_awards():
    # Load 5 sample diamond specs
    sample_keys = ["584392810", "LG612345678", "602384912", "LG598124095", "549210483"]
    dossiers = []

    for k in sample_keys:
        spec = IGIService.get_sample_report(k)
        quote = IndianMarketService.get_indian_wholesale_quote(spec)
        comps = ComparablesService.find_comparables(spec["carat"], spec["cut"], spec["color"], spec["clarity"])
        val = ValuationEngine.calculate_valuation(spec, 4000.0, comps, quote)
        dossiers.append({"diamond_spec": spec, "valuation": val})

    comparison = AIAssistantService.compare_5_reports(dossiers)
    
    assert comparison["total_evaluated"] == 5
    assert "awards" in comparison
    awards = comparison["awards"]
    assert "overall_pick" in awards
    assert "best_quality" in awards
    assert "best_value" in awards
    assert "best_buy" in awards
    assert "best_resale" in awards
    assert len(comparison["comparison_matrix"]) == 5
