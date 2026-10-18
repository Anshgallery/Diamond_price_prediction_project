import pytest
import json
import uuid
from app import app
from DiamondPricePrediction.services.ai_trade_advisor_agent import AITradeAdvisorAgent
from DiamondPricePrediction.services.ai_assistant_service import AIAssistantService

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

def test_tool_execution_suite():
    """Validates that all LLM tools execute correctly and return structured outputs."""
    # 1. Bullion Rates Tool
    bullion = AITradeAdvisorAgent.execute_tool("get_live_bullion_rates", {})
    assert bullion["success"] is True
    assert "rates_per_10g" in bullion
    assert "24K" in bullion["rates_per_10g"]
    assert "18K" in bullion["rates_per_10g"]

    # 2. Diamond Market Quote Tool
    quote = AITradeAdvisorAgent.execute_tool("get_diamond_market_quote", {
        "carat": 1.02,
        "color": "E",
        "clarity": "VVS1",
        "cut": "Ideal",
        "origin_type": "Natural"
    })
    assert quote["success"] is True
    assert quote["total_wholesale_inr"] > 0
    assert quote["price_per_carat_inr"] > 0
    assert "Bharat Diamond Bourse" in quote["source"]

    # 3. Lab-Grown Quote Tool
    quote_lgd = AITradeAdvisorAgent.execute_tool("get_diamond_market_quote", {
        "carat": 2.0,
        "color": "D",
        "clarity": "VVS2",
        "cut": "Ideal",
        "origin_type": "Lab-Grown"
    })
    assert quote_lgd["success"] is True
    assert quote_lgd["total_wholesale_inr"] > 0
    assert "Surat Diamond Bourse" in quote_lgd["source"]

    # 4. Jewellery Calculation Tool
    calc = AITradeAdvisorAgent.execute_tool("calculate_jewellery_quotation", {
        "net_gold_weight": 8.5,
        "purity": "18K",
        "wastage_pct": 5.0,
        "diamond_carat": 1.0,
        "diamond_rate_per_carat": 150000.0,
        "making_charge_per_gram": 750.0,
        "retail_markup_pct": 25.0
    })
    assert calc["success"] is True
    assert calc["landed_cost_inr"] > 0
    assert calc["grand_total_inr"] > 0
    assert calc["total_gst_3pct_inr"] > 0

    # 5. IGI Report Lookup Tool
    igi = AITradeAdvisorAgent.execute_tool("lookup_igi_report", {"report_number": "584392810"})
    assert igi["success"] is True
    assert igi["carat"] == 1.02
    assert igi["color"] == "E"

    # 6. Cut Proportions Tool
    prop = AITradeAdvisorAgent.execute_tool("analyze_cut_proportions", {
        "table": 56.5,
        "depth": 61.8,
        "x": 6.46,
        "y": 6.49,
        "z": 4.00
    })
    assert prop["success"] is True
    assert "proportion_evaluation" in prop
    assert prop["proportion_evaluation"]["overall_proportion_score"] >= 80

def test_conversation_memory_lifecycle():
    """Validates multi-turn memory recording, retrieval, and reset."""
    test_session = f"test-session-{uuid.uuid4()}"

    # Initial history empty
    hist0 = AITradeAdvisorAgent.get_conversation_history(test_session)
    assert len(hist0) == 0

    # Record user turn
    AITradeAdvisorAgent.record_message(test_session, role="user", content="What is the price of 1ct Natural F VS1?")
    # Record model turn with tools
    AITradeAdvisorAgent.record_message(
        test_session,
        role="model",
        content="Wholesale fair value is ₹3,20,000.",
        tools_executed=[{"tool": "get_diamond_market_quote", "output": {"price": 320000}}]
    )

    hist1 = AITradeAdvisorAgent.get_conversation_history(test_session)
    assert len(hist1) == 2
    assert hist1[0]["role"] == "user"
    assert hist1[1]["role"] == "model"
    assert len(hist1[1]["tools_executed"]) == 1

    # Reset session
    AITradeAdvisorAgent.reset_session(test_session)
    hist2 = AITradeAdvisorAgent.get_conversation_history(test_session)
    assert len(hist2) == 0

def test_autonomous_reasoning_and_chat_flow():
    """Validates end-to-end chat response with dynamic trade calculations and risk assessment."""
    test_session = f"chat-session-{uuid.uuid4()}"
    query = "A dealer is asking ₹5,00,000 for a 1.50ct F VS1 Natural diamond. Should I buy it?"

    res = AITradeAdvisorAgent.chat(query, session_id=test_session)
    assert res["success"] is True
    assert "reply" in res
    assert len(res["reply"]) > 100
    assert "tools_executed" in res
    assert len(res["tools_executed"]) >= 1

    reply = res["reply"]
    # Check that it executed tools and produced structured advice
    assert "Wholesale" in reply or "Benchmark" in reply
    assert "Counter-Offer" in reply or "Target" in reply
    assert "Risk" in reply or "Quality" in reply

    # Verify message recorded in memory
    hist = AITradeAdvisorAgent.get_conversation_history(test_session)
    assert len(hist) == 2  # user + model

def test_chat_api_endpoints(client):
    """Validates HTTP endpoints /api/chat, /api/chat/history, and /api/chat/reset."""
    session_id = f"api-test-{uuid.uuid4()}"

    # 1. Post chat message
    res = client.post("/api/chat", json={
        "message": "What are current 18K and 22K IBJA gold rates?",
        "session_id": session_id
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "reply" in data
    assert "IBJA" in data["reply"] or "Gold" in data["reply"]
    assert len(data["tools_executed"]) >= 1

    # 2. Fetch history
    res_hist = client.get(f"/api/chat/history?session_id={session_id}")
    assert res_hist.status_code == 200
    hist_data = res_hist.get_json()
    assert hist_data["success"] is True
    assert len(hist_data["history"]) >= 2

    # 3. Reset history
    res_reset = client.post("/api/chat/reset", json={"session_id": session_id})
    assert res_reset.status_code == 200
    assert res_reset.get_json()["success"] is True

    # 4. Verify cleared
    res_hist_after = client.get(f"/api/chat/history?session_id={session_id}")
    assert len(res_hist_after.get_json()["history"]) == 0

    # 5. Assistant page GET
    res_page = client.get("/assistant")
    assert res_page.status_code == 200
    assert b"AI Trade Advisor" in res_page.data
    assert b"chatMessagesFeed" in res_page.data
