import pytest
from DiamondPricePrediction.services.igi_service import IGIService

def test_igi_verification_link_generation():
    # Test valid natural IGI number
    info_nat = IGIService.get_verification_info("584392810")
    assert info_nat["portal_ready"] is True
    assert "584392810" in info_nat["report_check_url"]
    assert info_nat["report_number"] == "584392810"

    # Test valid lab-grown IGI number
    info_lg = IGIService.get_verification_info("LG612345678")
    assert info_lg["portal_ready"] is True
    assert "LG612345678" in info_lg["report_check_url"]

    # Test missing / invalid report number
    info_inv = IGIService.get_verification_info("")
    assert info_inv["verified"] is False
    assert info_inv["report_check_url"] is None

def test_igi_sample_reports():
    samples = IGIService.get_all_samples()
    assert len(samples) >= 4

    sample_nat = IGIService.get_sample_report("584392810")
    assert sample_nat is not None
    assert sample_nat["origin_type"] == "Natural"
    assert sample_nat["carat"] == 1.02
    assert sample_nat["color"] == "E"
    assert sample_nat["clarity"] == "VVS1"

    sample_lg = IGIService.get_sample_report("LG612345678")
    assert sample_lg is not None
    assert sample_lg["origin_type"] == "Lab-Grown"
    assert sample_lg["carat"] == 2.04
    assert sample_lg["color"] == "D"

def test_igi_text_parsing():
    sample_text = """
    INTERNATIONAL GEMOLOGICAL INSTITUTE
    IGI REPORT NUMBER 584392810
    Natural Diamond Report
    Round Brilliant
    Measurements: 6.46 - 6.49 x 4.00 mm
    Carat Weight: 1.02 CARAT
    Color Grade: E
    Clarity Grade: VVS1
    Cut Grade: Ideal
    Polish: Excellent
    Symmetry: Excellent
    Fluorescence: None
    Table: 56.5%
    Total Depth: 61.8%
    Laserscribe: IGI 584392810
    """
    res = IGIService.parse_igi_text(sample_text)
    assert res["success"] is True
    norm = res["normalized"]
    assert norm["report_number"] == "584392810"
    assert norm["origin_type"] == "Natural"
    assert norm["carat"] == 1.02
    assert norm["color"] == "E"
    assert norm["clarity"] == "VVS1"
    assert norm["cut"] == "Ideal"
    assert norm["table"] == 56.5
    assert norm["depth"] == 61.8
