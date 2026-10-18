import pytest
from decimal import Decimal
from DiamondPricePrediction.services.jewellery_calculator import JewelleryCalculator
from DiamondPricePrediction.services.invoice_service import InvoiceService
from DiamondPricePrediction.services.invoice_pdf_generator import InvoicePdfGenerator
from DiamondPricePrediction.services.einvoice_service import EInvoiceService

def test_decimal_jewellery_calculator_precision():
    """Verify that financial arithmetic uses exact Decimal rounding and no IEEE 754 float drift."""
    params = {
        "metal_type": "gold",
        "purity": "18K",
        "base_rate": 7850.0,
        "net_weight": 5.0,
        "wastage_pct": 5.0,
        "enable_diamond": True,
        "diamond_carat": 1.02,
        "diamond_cost": 300000.0,
        "making_mode": "per_gram",
        "making_val": 850.0,
        "setting_mode": "per_stone",
        "setting_val": 50.0,
        "hallmark_fee": 45.0,
        "misc_labour": 1000.0,
        "markup_pct": 25.0,
        "discount_mode": "percentage",
        "discount_val": 5.0,
        "gst_rate": 3.0,
        "is_interstate": False
    }

    res = JewelleryCalculator.calculate(params)

    # 5.0g net + 5% wastage = 5.25g gross
    assert res["gross_weight_grams"] == 5.25
    # 18K rate = 7850 * (18/24) = 5887.50
    assert res["metal_rate_per_g"] == 5887.50
    # 5.25 * 5887.50 = 30909.38
    assert res["metal_cost"] == 30909.38

    # Making: 5.25 * 850 = 4462.50. Setting: 1 stone * 50 = 50. Total = 4512.50
    assert res["making_charge"] == 4462.50
    assert res["setting_charge"] == 50.0
    assert res["total_making_setting"] == 4512.50

    # Total landed cost = 30909.38 + 300000 + 0 + 4462.50 + 50 + 45 + 1000 = 336466.88
    assert res["landed_cost"] == 336466.88

    # Retail pre-discount = 336466.88 * 1.25 = 420583.60
    assert res["retail_pre_discount"] == 420583.60

    # 5% Discount = 420583.60 * 0.05 = 21029.18
    assert res["discount_amount"] == 21029.18

    # Taxable amount = 420583.60 - 21029.18 = 399554.42
    assert res["taxable_amount"] == 399554.42

    # 3% GST: CGST 1.5% = 5993.32, SGST 1.5% = 5993.32, Total GST = 11986.64
    assert res["cgst_amount"] == 5993.32
    assert res["sgst_amount"] == 5993.32
    assert res["total_gst"] == 11986.64

    # Grand total = 399554.42 + 11986.64 = 411541.06
    assert res["grand_total"] == 411541.06

    # Profit = 399554.42 - 336466.88 = 63087.54
    assert res["profit_amount"] == 63087.54

    # Realized Margin % = (63087.54 / 399554.42) * 100 = 15.8%
    assert res["margin_pct"] == 15.8

    # Check words representation (contains "Four Lakh" and "Indian Rupee")
    assert "Four Lakh" in res["amount_in_words"]
    assert "Indian Rupee" in res["amount_chargeable_words"]
    assert "Indian Rupee" in res["tax_amount_words"]

    # Verify structured line items and HSN table exist
    assert len(res["line_items"]) >= 2
    assert len(res["hsn_summary"]) >= 1

def test_all_five_materials_supported():
    """Verify that Gold, Silver, Platinum, Diamond, and Ruby are fully calculated with accurate HSN."""
    InvoiceService.init_db()

    # 1. Gold (22K)
    res_gold = JewelleryCalculator.calculate({
        "metal_type": "gold", "purity": "22K", "net_weight": 20.0, "wastage_pct": 0.0,
        "making_val": 500.0, "enable_diamond": False, "enable_gemstone": False
    })
    assert res_gold["metal_category"] == "Gold"
    assert any(item["hsn"] == "7113" for item in res_gold["line_items"])

    # 2. Silver (Sterling Silver 925)
    res_silver = JewelleryCalculator.calculate({
        "metal_type": "silver", "purity": "925", "net_weight": 50.0, "wastage_pct": 0.0,
        "making_val": 50.0, "enable_diamond": False, "enable_gemstone": False
    })
    assert res_silver["metal_category"] == "Silver"
    assert res_silver["metal_cost"] > 0

    # 3. Platinum (Pt950)
    res_plat = JewelleryCalculator.calculate({
        "metal_type": "platinum", "purity": "Pt950", "net_weight": 10.0, "wastage_pct": 0.0,
        "making_val": 800.0, "enable_diamond": False, "enable_gemstone": False
    })
    assert res_plat["metal_category"] == "Platinum"
    assert res_plat["metal_cost"] > 0

    # 4. Diamond
    res_dia = JewelleryCalculator.calculate({
        "metal_type": "gold", "purity": "18K", "net_weight": 3.0,
        "enable_diamond": True, "diamond_carat": 1.5, "diamond_cost": 350000.0
    })
    assert any(item["hsn"] == "7102" for item in res_dia["line_items"])

    # 5. Ruby
    res_ruby = JewelleryCalculator.calculate({
        "metal_type": "gold", "purity": "18K", "net_weight": 5.0,
        "enable_gemstone": True, "gem_type": "Natural Pigeon Blood Ruby", "gem_carat": 2.5, "gem_cost": 65000.0
    })
    assert res_ruby["enable_gemstone"] is True
    assert any(item["hsn"] == "7103" for item in res_ruby["line_items"])

def test_einvoice_irn_and_qr_compliance():
    """Verify that EInvoiceService produces standard 64-char IRN, 15-digit Ack No, and scannable QR payload."""
    supplier_gstin = "27AABCS1429B1Z8"
    buyer_gstin = "29AAFFC8126N1ZZ"
    doc_no = "GF-2026-0001"
    doc_date = "18-Oct-26"
    grand_total = 4130.0

    pkg = EInvoiceService.get_full_einvoice_package(
        supplier_gstin=supplier_gstin,
        buyer_gstin=buyer_gstin,
        doc_no=doc_no,
        doc_date_str=doc_date,
        grand_total=grand_total,
        item_count=1
    )

    # 64-character SHA-256 hex string
    assert len(pkg["irn"]) == 64
    assert pkg["irn"].isalnum()

    # 15-digit Ack No
    assert len(pkg["ack_no"]) == 15
    assert pkg["ack_no"].startswith("112")

    # State code resolution
    assert pkg["seller_state"] == "Maharashtra"
    assert pkg["seller_state_code"] == "27"
    assert pkg["buyer_state"] == "Karnataka"
    assert pkg["buyer_state_code"] == "29"

    # Scannable QR SVG Data URI
    assert pkg["qr_svg_data_uri"].startswith("data:image/svg+xml;base64,")

def test_interstate_gst_calculation():
    """Verify that inter-state sales apply IGST 3% instead of CGST+SGST split."""
    params = {
        "metal_type": "gold",
        "purity": "22K",
        "base_rate": 7850.0,
        "net_weight": 10.0,
        "wastage_pct": 0.0,
        "enable_diamond": False,
        "markup_pct": 10.0,
        "gst_rate": 3.0,
        "is_interstate": True
    }
    res = JewelleryCalculator.calculate(params)
    assert res["is_interstate"] is True
    assert res["cgst_amount"] == 0.0
    assert res["sgst_amount"] == 0.0
    assert res["igst_amount"] == res["total_gst"]

def test_invoice_service_crud_and_share_link():
    """Verify persistent SQLite invoice storage, sequential numbering, and share links."""
    InvoiceService.init_db()

    form_data = {
        "customer_name": "Pooja Singhania",
        "customer_phone": "+91 98111 22334",
        "customer_email": "pooja@singhania.com",
        "customer_address": "Worli Sea Face, Mumbai",
        "customer_pan": "ASDFG1234H",
        "metal_type": "gold",
        "purity": "18K",
        "net_weight": "6.0",
        "wastage_pct": "5.0",
        "enable_diamond": "true",
        "diamond_carat": "1.50",
        "diamond_cost": "450000",
        "making_mode": "per_gram",
        "making_val": "900",
        "markup_pct": "25.0",
        "discount_val": "0.0"
    }

    create_res = InvoiceService.create_invoice(form_data, jeweller_id="test_jeweller")
    assert create_res["success"] is True
    assert create_res["invoice_number"].startswith("GF-")
    assert len(create_res["share_token"]) >= 16

    inv_id = create_res["invoice_id"]
    share_token = create_res["share_token"]

    # Fetch by ID
    by_id = InvoiceService.get_invoice_by_id(inv_id)
    assert by_id is not None
    assert by_id["customer_name"] == "Pooja Singhania"
    assert by_id["status"] == "Issued"
    assert by_id["profit_amount"] > 0
    assert "calc" in by_id
    assert "einvoice" in by_id
    assert "dispatch" in by_id

    # Fetch by Share Token
    by_share = InvoiceService.get_invoice_by_share_token(share_token)
    assert by_share is not None
    assert by_share["id"] == inv_id
    assert by_share["customer_name"] == "Pooja Singhania"

    # Update Status
    updated = InvoiceService.update_status(inv_id, "Paid", jeweller_id="test_jeweller")
    assert updated is True
    refetched = InvoiceService.get_invoice_by_id(inv_id)
    assert refetched["status"] == "Paid"

    # List Invoices
    all_invs = InvoiceService.list_invoices(jeweller_id="test_jeweller")
    assert any(i["id"] == inv_id for i in all_invs)

    # Delete Invoice
    deleted = InvoiceService.delete_invoice(inv_id, jeweller_id="test_jeweller")
    assert deleted is True
    assert InvoiceService.get_invoice_by_id(inv_id) is None

def test_invoice_pdf_generation_customer_and_internal_modes():
    """Verify that ReportLab generates valid, strictly B&W A4 portrait PDF for both customer and internal store copy."""
    InvoiceService.init_db()
    create_res = InvoiceService.create_invoice({
        "customer_name": "Rohan Deshmukh",
        "customer_phone": "+91 98222 33445",
        "metal_type": "gold",
        "purity": "18K",
        "net_weight": 4.0,
        "wastage_pct": 5.0,
        "enable_diamond": True,
        "diamond_carat": 1.0,
        "diamond_cost": 250000,
        "enable_gemstone": True,
        "gem_type": "Ruby (Manik)",
        "gem_carat": 2.0,
        "gem_cost": 40000,
        "making_mode": "fixed",
        "making_val": 3500,
        "markup_pct": 20.0
    }, jeweller_id="pdf_test")

    invoice = InvoiceService.get_invoice_by_id(create_res["invoice_id"])
    assert invoice is not None

    # Customer View PDF
    cust_pdf = InvoicePdfGenerator.generate_invoice_pdf(invoice, is_internal=False)
    assert isinstance(cust_pdf, bytes)
    assert len(cust_pdf) > 2000
    assert cust_pdf.startswith(b"%PDF-")

    # Internal Store Copy PDF
    int_pdf = InvoicePdfGenerator.generate_invoice_pdf(invoice, is_internal=True)
    assert isinstance(int_pdf, bytes)
    assert len(int_pdf) > len(cust_pdf)  # Includes store audit margins & landed cost table
    assert int_pdf.startswith(b"%PDF-")
