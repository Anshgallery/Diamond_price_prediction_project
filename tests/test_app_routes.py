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
    assert b"Fair Buy Price" in res_get.data or b"Suggested Jeweller Buy" in res_get.data
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

def test_pdf_routes(client):
    # Serve inline PDF
    res_pdf = client.get("/pdf/584392810")
    assert res_pdf.status_code == 200
    assert res_pdf.content_type == "application/pdf"
    assert res_pdf.data.startswith(b"%PDF")

    # Download PDF
    res_download = client.get("/download-pdf/584392810")
    assert res_download.status_code == 200
    assert res_download.content_type == "application/pdf"
    assert "attachment" in res_download.headers.get("Content-Disposition", "")
    assert res_download.data.startswith(b"%PDF")

def test_save_to_workshop_endpoint(client):
    import json
    spec = {"report_number": "584392810", "carat": 1.02, "color": "E", "clarity": "VVS1", "cut": "Ideal", "origin_type": "Natural"}
    val = {"suggested_buy_price": 300000, "suggested_sell_price": 375000, "fair_market_value": 340000}
    
    res = client.post("/inventory/save-to-workshop", data={
        "diamond_spec_json": json.dumps(spec),
        "valuation_json": json.dumps(val),
        "buying_price_inr": "300000",
        "selling_price_inr": "375000"
    }, follow_redirects=True)
    
    assert res.status_code == 200
    assert b"successfully saved to Workshop" in res.data or b"Workshop" in res.data

def test_ibja_rates_api(client):
    res = client.get("/api/ibja-rates")
    assert res.status_code == 200
    data = res.get_json()
    assert "rates" in data
    assert "24K" in data["rates"]
    assert "22K" in data["rates"]
    assert "18K" in data["rates"]
    assert "14K" in data["rates"]
    assert "Silver_999" in data["rates"]
    assert "publication_timestamp" in data
    assert "source" in data

def test_calculate_jewellery_api(client):
    payload = {
        "net_gold_weight": 8.5,
        "purity_str": "18K",
        "wastage_pct": 5.0,
        "custom_gold_rate": 70000,
        "diamond_carat": 0.75,
        "diamond_rate_per_carat": 120000,
        "gemstone_cost": 5000,
        "making_charge_per_gram": 650,
        "hallmarking_fee": 45,
        "retail_markup_pct": 18.0,
        "discount_pct": 2.0,
        "is_interstate": False
    }
    res = client.post("/api/calculate-jewellery", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    calc = data["data"]
    assert "landed_cost" in calc
    assert "grand_total" in calc
    assert "cgst_amount" in calc
    assert "sgst_amount" in calc
    assert calc["cgst_amount"] == calc["sgst_amount"]
    assert calc["total_gst"] > 0
    assert calc["profit_amount"] > 0
    assert calc["margin_pct"] > 0

def test_invoices_full_lifecycle(client):
    from DiamondPricePrediction.services.invoice_service import InvoiceService

    # 1. Access invoices ledger
    res_list = client.get("/invoices")
    assert res_list.status_code == 200
    assert b"Bill History" in res_list.data or b"Tax Invoices" in res_list.data

    # 2. Create invoice
    invoice_payload = {
        "customer_name": "Deepak Verma",
        "customer_phone": "+91 98765 43210",
        "customer_email": "deepak@example.com",
        "customer_address": "404, Bandra West, Mumbai 400050",
        "customer_state": "Maharashtra",
        "customer_pan": "ABCDE1234F",
        "item_title": "18K Diamond Solitaire Engagement Ring",
        "jewellery_type": "Ring",
        "hsn_code": "7113",
        "purity": "18K",
        "gross_weight": "9.200",
        "net_gold_weight": "8.500",
        "wastage_pct": "5.00",
        "gold_rate": "72000.00",
        "diamond_carat": "0.700",
        "diamond_rate_per_carat": "125000.00",
        "diamond_clarity": "VVS1",
        "diamond_color": "F",
        "diamond_cut": "Ideal",
        "diamond_origin": "Natural",
        "diamond_cert_number": "584392810",
        "gemstone_name": "Emerald Accent",
        "gemstone_weight": "0.300",
        "gemstone_cost": "4500.00",
        "making_type": "per_gram",
        "making_rate": "700.00",
        "hallmarking_fee": "45.00",
        "certification_fee": "2500.00",
        "retail_markup_pct": "18.00",
        "discount_pct": "3.00",
        "is_interstate": "0",
        "notes": "Complimentary yearly ultrasonic cleaning included."
    }

    res_create = client.post("/invoice/create", data=invoice_payload, follow_redirects=True)
    assert res_create.status_code == 200
    assert b"Deepak Verma" in res_create.data
    assert b"GF-" in res_create.data

    # Retrieve created invoice from db
    invoices = InvoiceService.list_invoices(jeweller_id="default", limit=1)
    assert len(invoices) >= 1
    inv = invoices[0]
    inv_id = inv["id"]
    share_token = inv["share_token"]

    # 3. View internal invoice
    res_view = client.get(f"/invoice/{inv_id}")
    assert res_view.status_code == 200
    assert b"Confidential Jeweller Metrics" in res_view.data or b"Margin" in res_view.data
    assert b"Direct Print" in res_view.data
    assert b"Download PDF" in res_view.data

    # 4. Download PDF from internal view
    res_pdf = client.get(f"/invoice/{inv_id}/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.content_type == "application/pdf"
    assert res_pdf.data.startswith(b"%PDF")
    assert inv['invoice_number'] in res_pdf.headers.get("Content-Disposition", "")

    # 5. Access public share link (Confidential metrics MUST NOT be present)
    res_share = client.get(f"/invoice/share/{share_token}")
    assert res_share.status_code == 200
    assert b"Deepak Verma" in res_share.data
    assert b"Confidential Jeweller Metrics" not in res_share.data
    assert b"Profit" not in res_share.data
    assert b"Landed Cost" not in res_share.data

    # 6. Public share PDF download
    res_share_pdf = client.get(f"/invoice/share/{share_token}/pdf")
    assert res_share_pdf.status_code == 200
    assert res_share_pdf.content_type == "application/pdf"
    assert res_share_pdf.data.startswith(b"%PDF")

    # 7. Update status to Paid
    res_status = client.post(f"/invoice/{inv_id}/status", data={"status": "Paid"}, follow_redirects=True)
    assert res_status.status_code == 200
    updated_inv = InvoiceService.get_invoice_by_id(inv_id)
    assert updated_inv["status"] == "Paid"

    # 8. Delete invoice
    res_delete = client.post(f"/invoice/{inv_id}/delete", follow_redirects=True)
    assert res_delete.status_code == 200
    assert InvoiceService.get_invoice_by_id(inv_id) is None


def test_api_bullion_rates_and_sync(client):
    """Verify JSON endpoints for Bullions.co.in rates and live synchronization."""
    # 1. Test /api/bullion-rates
    res = client.get("/api/bullion-rates")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "rates_per_gram" in data
    assert "24K" in data["rates_per_gram"]
    assert "Silver_999" in data["rates_per_gram"]
    assert data["bullions_url"] == "https://bullions.co.in/"
    assert data["ibja_url"] == "https://www.ibja.co/"
    assert data["status"] in ["LIVE", "STALE"]

    # 2. Test /api/bullion/sync
    res_sync = client.post("/api/bullion/sync")
    assert res_sync.status_code == 200
    sync_data = res_sync.get_json()
    assert sync_data["success"] is True
    assert sync_data["synced"] is True
    assert "rates_per_gram" in sync_data
    assert sync_data["rates_per_gram"]["24K"] > 0
    assert sync_data["rates_per_gram"]["Silver_999"] > 0



