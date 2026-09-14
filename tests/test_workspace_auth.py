import pytest
import uuid
from DiamondPricePrediction.services.auth_service import AuthService
from DiamondPricePrediction.services.inventory_service import InventoryService
from DiamondPricePrediction.services.igi_service import IGIService
from DiamondPricePrediction.services.indian_market_service import IndianMarketService
from DiamondPricePrediction.services.valuation_engine import ValuationEngine
from DiamondPricePrediction.services.comparables_service import ComparablesService

def test_jeweller_registration_and_authentication():
    unique_email = f"test_{uuid.uuid4().hex[:6]}@jeweller.com"
    pwd = "securepassword123"

    reg = AuthService.register_jeweller(
        business_name="Surat Solitaires Ltd",
        owner_name="Bhavesh Patel",
        email=unique_email,
        password=pwd,
        city="Surat",
        gst_number="24AAACS1234F1Z8"
    )
    assert reg["success"] is True
    assert reg["jeweller"]["email"] == unique_email

    # Authenticate with valid password
    auth = AuthService.authenticate(unique_email, pwd)
    assert auth is not None
    assert auth["business_name"] == "Surat Solitaires Ltd"

    # Authenticate with wrong password
    bad_auth = AuthService.authenticate(unique_email, "wrongpassword")
    assert bad_auth is None

def test_inventory_crud_and_stats():
    spec = IGIService.get_sample_report("584392810")
    quote = IndianMarketService.get_indian_wholesale_quote(spec)
    comps = ComparablesService.find_comparables(spec["carat"], spec["cut"], spec["color"], spec["clarity"])
    val = ValuationEngine.calculate_valuation(spec, 4000.0, comps, quote)

    item_id = InventoryService.save_diamond(
        diamond_spec=spec,
        valuation_result=val,
        buying_price_inr=350000,
        status="In Stock",
        tag="Inventory",
        jeweller_id="test_user"
    )

    assert item_id is not None
    retrieved = InventoryService.get_diamond_by_id(item_id)
    assert retrieved is not None
    assert retrieved["report_number"] == "584392810"

    items = InventoryService.get_inventory(jeweller_id="test_user")
    assert len(items) >= 1

    stats = InventoryService.get_summary_stats(jeweller_id="test_user")
    assert stats["inventory_count"] >= 1
    assert stats["total_portfolio_market_inr"] > 0

    # Cleanup
    deleted = InventoryService.delete_diamond(item_id)
    assert deleted is True
