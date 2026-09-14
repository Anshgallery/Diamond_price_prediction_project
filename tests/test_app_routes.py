import os
import sys
import pytest
from app import app
from DiamondPricePrediction.services.igi_service import IGIService

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

def test_homepage_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"GEMFORECAST" in res.data
    assert b"IGI Diamond AI Valuation" in res.data

def test_appraise_get_and_post_endpoints(client):
    # GET with sample IGI
    res_get = client.get("/appraise?report_number=584392810")
    assert res_get.status_code == 200
    assert b"584392810" in res_get.data
    assert b"Suggested Jeweller Buy" in res_get.data
    assert b"Customer Total with 3% GST" in res_get.data

    # POST with sample IGI
    res_post = client.post("/appraise", data={"report_number": "LG612345678", "asking_price_inr": "55000"})
    assert res_post.status_code == 200
    assert b"LG612345678" in res_post.data
    assert b"Lab-Grown" in res_post.data

def test_compare_endpoint(client):
    # GET 5-report sample comparison
    res = client.get("/compare?sample=true")
    assert res.status_code == 200
    assert b"5-Report" in res.data
    assert b"Overall Jeweller Pick" in res.data
    assert b"Best Gemological Quality" in res.data

def test_workspace_endpoint(client):
    res = client.get("/workspace")
    assert res.status_code == 200
    assert b"Jeweller" in res.data

def test_calculator_endpoint(client):
    res = client.get("/calculator")
    assert res.status_code == 200
    assert b"Profit &amp; 3% GST" in res.data or b"Profit & 3% GST" in res.data

def test_assistant_endpoint(client):
    res_get = client.get("/assistant")
    assert res_get.status_code == 200

    res_post = client.post("/assistant", data={"query": "What should I ask for a 1ct Natural stone?"})
    assert res_post.status_code == 200
    assert b"Retail Pricing" in res_post.data or b"Advisory" in res_post.data

def test_market_rates_endpoint(client):
    res = client.get("/market-rates")
    assert res.status_code == 200
    assert b"Bharat Diamond Bourse" in res.data
    assert b"Surat Diamond Bourse" in res.data
