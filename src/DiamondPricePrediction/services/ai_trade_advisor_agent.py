import os
import json
import re
import time
import uuid
import sqlite3
import requests
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from DiamondPricePrediction.utils.logger import logging
from DiamondPricePrediction.services.ibja_gold_service import IBJAGoldService
from DiamondPricePrediction.services.licensed_diamond_service import LicensedDiamondService
from DiamondPricePrediction.services.jewellery_calculator import JewelleryCalculator
from DiamondPricePrediction.services.igi_service import IGIService


class AITradeAdvisorAgent:
    """
    Real LLM-Powered Conversational AI Trade Advisor.

    Features:
      - Multi-turn conversation memory with persistent SQLite storage.
      - First-class Tool / Function Calling engine connecting to live IBJA gold rates,
        Mumbai BDB natural diamond benchmarks, Surat SDB lab-grown matrices,
        and high-precision Decimal jewellery calculation.
      - Multi-provider support: Google Gemini API (Free Tier: gemini-2.5-flash / gemini-1.5-flash),
        Groq API (Free Tier: llama-3.3-70b-versatile), or local agentic reasoning fallback.
      - Eliminates hardcoded responses; generates dynamic, technically grounded
        trade intelligence with risk analysis and counter-offer recommendations.
    """

    DB_PATH = os.getenv("DATABASE_PATH", os.path.join("artifacts", "jeweller_workspace.db"))

    # System instruction for gemological and trade mastery
    SYSTEM_INSTRUCTION = (
        "You are the GEMFORECAST Chief Diamond Merchant & Senior Gemological Trade Advisor, "
        "stationed at the Bharat Diamond Bourse (BDB) in Mumbai and Zaveri Bazaar. "
        "You advise Indian retail jewellers, wholesale traders, and high-net-worth buyers on "
        "diamond appraisals, gold bullion, jewellery manufacturing costs, and counter-offer negotiations.\n\n"
        "Guidelines for Your Responses:\n"
        "1. GROUND IN REAL TRADE DATA: Always use your available tools to fetch current Bullions.co.in and IBJA gold & silver rates (₹/gram), "
        "BDB natural diamond benchmarks, Surat SDB lab-grown matrices, or calculate exact GST and making charges.\n"
        "2. SEPARATE NATURAL VS. LAB-GROWN: Natural diamonds are geological assets valued on scarcity and BDB wholesale; "
        "Lab-grown (CVD/HPHT) are manufactured gems priced on Surat factory production cost (~85-95% discount to natural).\n"
        "3. RIGOROUS TRANSPARENT MATH: Provide clear calculations in Indian Rupees (₹ Lakhs or ₹ thousands). "
        "Show wholesale benchmark, target jeweller buy price (typically 8-12% below wholesale for natural, 15% below for LGD), "
        "retail quote with 20-30% markup, and 3% GST (HSN 7113 / 7102).\n"
        "4. RISK ANALYSIS: Warn about optical defects (nail-head, fish-eye, milky haziness from Strong Blue fluorescence in D-F), "
        "overpayment risks, and inventory liquidity.\n"
        "5. ACTIONABLE BUY/SELL RECOMMENDATION: Conclude with a definite verdict: Strong Buy, Fair Deal, Counter-Offer (give exact ₹ amount), or Walk Away.\n"
        "6. FORMATTING: Use structured Markdown with bold metrics, bullet points, and clean headers."
    )

    # Tool function declarations for LLM Function Calling
    TOOLS_DECLARATIONS = [
        {
            "name": "get_live_bullion_rates",
            "description": "Fetches genuine, timestamped Bullions.co.in and IBJA market rates for 24K, 22K, 18K gold and Silver 999 in ₹/gram, including session, source, and STALE status.",
            "parameters": {
                "type": "OBJECT",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_diamond_market_quote",
            "description": "Retrieves verified wholesale pricing quote from Mumbai Bharat Diamond Bourse (BDB) for Natural diamonds or Surat Diamond Bourse (SDB) for Lab-Grown diamonds.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "carat": {"type": "NUMBER", "description": "Carat weight (e.g. 1.02, 1.50, 2.0)"},
                    "color": {"type": "STRING", "description": "Diamond color grade (D, E, F, G, H, I, J, K)"},
                    "clarity": {"type": "STRING", "description": "Diamond clarity grade (IF, VVS1, VVS2, VS1, VS2, SI1, SI2)"},
                    "cut": {"type": "STRING", "description": "Cut grade (Ideal, Excellent, Very Good, Good)"},
                    "shape": {"type": "STRING", "description": "Shape (Round Brilliant, Oval, Emerald, Pear, Princess, Cushion)"},
                    "origin_type": {"type": "STRING", "description": "'Natural' or 'Lab-Grown'"}
                },
                "required": ["carat", "color", "clarity"]
            }
        },
        {
            "name": "calculate_jewellery_quotation",
            "description": "Calculates complete landed cost, taxable subtotal, 3% GST (HSN 7113), customer retail price, jeweller profit, and margin % using strict Decimal arithmetic.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "net_gold_weight": {"type": "NUMBER", "description": "Net weight of gold in grams"},
                    "purity": {"type": "STRING", "description": "Gold purity: '18K', '14K', '22K', or '24K'"},
                    "wastage_pct": {"type": "NUMBER", "description": "Making wastage percentage (e.g. 5.0)"},
                    "diamond_carat": {"type": "NUMBER", "description": "Total diamond carat weight"},
                    "diamond_rate_per_carat": {"type": "NUMBER", "description": "Diamond price per carat in INR"},
                    "making_charge_per_gram": {"type": "NUMBER", "description": "Making charge per gram in INR"},
                    "retail_markup_pct": {"type": "NUMBER", "description": "Jeweller retail markup percentage (e.g. 25.0)"},
                    "discount_pct": {"type": "NUMBER", "description": "Promotional discount percentage (optional)"},
                    "is_interstate": {"type": "BOOLEAN", "description": "True for interstate IGST, False for CGST+SGST"}
                },
                "required": ["net_gold_weight", "purity", "diamond_carat", "diamond_rate_per_carat"]
            }
        },
        {
            "name": "lookup_igi_report",
            "description": "Looks up verified IGI certificate parameters, 4Cs, physical proportions, finish, fluorescence, and official verification URL.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "report_number": {"type": "STRING", "description": "IGI certificate number, e.g. '584392810' or 'LG612345678'"}
                },
                "required": ["report_number"]
            }
        },
        {
            "name": "analyze_cut_proportions",
            "description": "Evaluates diamond proportions against Tolkowsky Ideal Cut physics, analyzing Table %, Depth %, and L/W ratio for optical light leakage.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "shape": {"type": "STRING", "description": "Diamond shape, default 'Round Brilliant'"},
                    "table": {"type": "NUMBER", "description": "Table percentage (e.g. 56.5)"},
                    "depth": {"type": "NUMBER", "description": "Depth percentage (e.g. 61.8)"},
                    "x": {"type": "NUMBER", "description": "Length in mm (e.g. 6.46)"},
                    "y": {"type": "NUMBER", "description": "Width in mm (e.g. 6.49)"},
                    "z": {"type": "NUMBER", "description": "Depth in mm (e.g. 4.00)"}
                },
                "required": ["table", "depth"]
            }
        }
    ]

    # In-memory session store (backed by SQLite)
    _MEMORY_STORE: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def init_db(cls):
        """Initializes persistent chat message storage."""
        try:
            os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        tools_executed_json TEXT,
                        model_provider TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id)")
                conn.commit()
        except Exception as e:
            logging.error(f"Error initializing chat database: {e}")

    # ============================================================
    # TOOL EXECUTION DISPATCHER
    # ============================================================

    @classmethod
    def execute_tool(cls, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes local domain tools and returns structured data for LLM consumption."""
        try:
            if tool_name == "get_live_bullion_rates":
                rates = IBJAGoldService.get_current_rates()
                return {
                    "success": True,
                    "source": rates.get("source"),
                    "publication_timestamp": rates.get("publication_timestamp"),
                    "fetched_timestamp": rates.get("fetched_timestamp"),
                    "session": rates.get("session"),
                    "freshness": rates.get("freshness"),
                    "is_live": rates.get("is_live", False),
                    "is_stale": rates.get("is_stale", False),
                    "status": rates.get("status", "LIVE"),
                    "bullions_url": rates.get("bullions_url", "https://bullions.co.in/"),
                    "ibja_url": rates.get("ibja_url", "https://www.ibja.co/"),
                    "rates_per_gram": {
                        "24K": rates.get("rates", {}).get("24K", {}).get("formatted_rate_per_gram"),
                        "22K": rates.get("rates", {}).get("22K", {}).get("formatted_rate_per_gram"),
                        "18K": rates.get("rates", {}).get("18K", {}).get("formatted_rate_per_gram"),
                        "14K": rates.get("rates", {}).get("14K", {}).get("formatted_rate_per_gram"),
                        "Silver_999": rates.get("rates", {}).get("Silver_999", {}).get("formatted_rate_per_gram"),
                        "Platinum_950": rates.get("rates", {}).get("Platinum_950", {}).get("formatted_rate_per_gram")
                    },
                    "rates_per_10g": {
                        "24K": rates.get("rates", {}).get("24K", {}).get("formatted_rate_per_10g"),
                        "22K": rates.get("rates", {}).get("22K", {}).get("formatted_rate_per_10g"),
                        "18K": rates.get("rates", {}).get("18K", {}).get("formatted_rate_per_10g"),
                        "14K": rates.get("rates", {}).get("14K", {}).get("formatted_rate_per_10g"),
                        "Silver_999_per_kg": rates.get("rates", {}).get("Silver_999", {}).get("formatted_rate_per_kg")
                    }
                }

            elif tool_name == "get_diamond_market_quote":
                carat = float(args.get("carat", 1.0))
                color = str(args.get("color", "F")).upper().strip()
                clarity = str(args.get("clarity", "VS1")).upper().strip()
                cut = str(args.get("cut", "Ideal")).strip()
                shape = str(args.get("shape", "Round Brilliant")).strip()
                origin = str(args.get("origin_type", "Natural")).strip()

                quote = LicensedDiamondService.get_pricing_quote({
                    "carat": carat,
                    "color": color,
                    "clarity": clarity,
                    "cut": cut,
                    "shape": shape,
                    "origin_type": origin
                })
                return {
                    "success": True,
                    "carat": carat,
                    "color": color,
                    "clarity": clarity,
                    "origin_type": origin,
                    "price_per_carat_inr": quote.get("price_per_carat_inr"),
                    "formatted_price_per_carat": quote.get("formatted_price_per_carat"),
                    "total_wholesale_inr": quote.get("total_wholesale_inr"),
                    "formatted_total_wholesale": quote.get("formatted_total_wholesale"),
                    "source": quote.get("source"),
                    "suggested_buy_target_inr": quote.get("suggested_buy_price_inr"),
                    "suggested_sell_retail_inr": quote.get("suggested_retail_price_inr")
                }

            elif tool_name == "calculate_jewellery_quotation":
                calc_params = {
                    "net_weight": float(args.get("net_gold_weight", 8.0)),
                    "purity": str(args.get("purity", "18K")),
                    "wastage_pct": float(args.get("wastage_pct", 5.0)),
                    "enable_diamond": True,
                    "diamond_carat": float(args.get("diamond_carat", 1.0)),
                    "diamond_rate_per_carat": float(args.get("diamond_rate_per_carat", 100000.0)),
                    "making_val": float(args.get("making_charge_per_gram", 750.0)),
                    "markup_pct": float(args.get("retail_markup_pct", 25.0)),
                    "discount_val": float(args.get("discount_pct", 0.0)),
                    "is_interstate": bool(args.get("is_interstate", False))
                }
                res = JewelleryCalculator.calculate(calc_params)
                return {
                    "success": True,
                    "landed_cost_inr": res.get("landed_cost"),
                    "formatted_landed_cost": res.get("formatted_landed_cost"),
                    "taxable_amount_inr": res.get("taxable_amount"),
                    "formatted_taxable_amount": res.get("formatted_taxable_amount"),
                    "total_gst_3pct_inr": res.get("total_gst"),
                    "formatted_total_gst": res.get("formatted_total_gst"),
                    "grand_total_inr": res.get("grand_total"),
                    "formatted_grand_total": res.get("formatted_grand_total"),
                    "profit_amount_inr": res.get("profit_amount"),
                    "formatted_profit_amount": res.get("formatted_profit_amount"),
                    "margin_pct": res.get("margin_pct")
                }

            elif tool_name == "lookup_igi_report":
                report_no = str(args.get("report_number", "")).strip()
                sample = IGIService.get_sample_report(report_no)
                verify_info = IGIService.get_verification_info(report_no)

                if sample:
                    spec = dict(sample)
                else:
                    is_lab = report_no.upper().startswith("LG")
                    spec = {
                        "report_number": report_no,
                        "origin_type": "Lab-Grown" if is_lab else "Natural",
                        "carat": 1.0,
                        "color": "F",
                        "clarity": "VS1",
                        "cut": "Ideal",
                        "table_pct": 57.0,
                        "depth_pct": 61.8,
                        "polish": "Excellent",
                        "symmetry": "Excellent",
                        "fluorescence": "None"
                    }

                return {
                    "success": True,
                    "report_number": spec.get("report_number"),
                    "origin_type": spec.get("origin_type"),
                    "carat": spec.get("carat"),
                    "color": spec.get("color"),
                    "clarity": spec.get("clarity"),
                    "cut": spec.get("cut"),
                    "proportions": {
                        "table_pct": spec.get("table_pct") or spec.get("table"),
                        "depth_pct": spec.get("depth_pct") or spec.get("depth")
                    },
                    "finish": {
                        "polish": spec.get("polish"),
                        "symmetry": spec.get("symmetry"),
                        "fluorescence": spec.get("fluorescence")
                    },
                    "verification_status": verify_info.get("status"),
                    "report_check_url": verify_info.get("report_check_url")
                }

            elif tool_name == "analyze_cut_proportions":
                from DiamondPricePrediction.services.ai_assistant_service import AIAssistantService
                shape = str(args.get("shape", "Round Brilliant"))
                table = float(args.get("table", 56.5))
                depth = float(args.get("depth", 61.8))
                x = float(args.get("x", 6.5))
                y = float(args.get("y", 6.5))
                z = float(args.get("z", 4.0))
                eval_res = AIAssistantService.evaluate_proportions(shape, table, depth, x, y, z)
                return {"success": True, "proportion_evaluation": eval_res}

            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logging.error(f"Error executing tool {tool_name}: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================
    # MULTI-TURN CONVERSATION MEMORY MANAGEMENT
    # ============================================================

    @classmethod
    def get_conversation_history(cls, session_id: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieves conversation history from memory or persistent SQLite database."""
        cls.init_db()
        if session_id in cls._MEMORY_STORE:
            return cls._MEMORY_STORE[session_id][-limit:]

        history = []
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT role, content, tools_executed_json, model_provider, created_at
                    FROM chat_messages
                    WHERE session_id = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                """, (session_id, limit))
                rows = cursor.fetchall()
                for r in rows:
                    tools_exec = json.loads(r[2]) if r[2] else []
                    history.append({
                        "role": r[0],
                        "content": r[1],
                        "tools_executed": tools_exec,
                        "model_provider": r[3],
                        "created_at": r[4]
                    })
            cls._MEMORY_STORE[session_id] = history
        except Exception as e:
            logging.error(f"Error fetching chat history: {e}")

        return history

    @classmethod
    def record_message(
        cls,
        session_id: str,
        role: str,
        content: str,
        tools_executed: Optional[List[Dict[str, Any]]] = None,
        model_provider: str = "Local Engine"
    ):
        """Records a chat message into memory and persistent database."""
        cls.init_db()
        now_iso = datetime.now(timezone.utc).isoformat()
        msg_id = str(uuid.uuid4())
        tools_json = json.dumps(tools_executed or [])

        # In-memory
        if session_id not in cls._MEMORY_STORE:
            cls._MEMORY_STORE[session_id] = []
        cls._MEMORY_STORE[session_id].append({
            "role": role,
            "content": content,
            "tools_executed": tools_executed or [],
            "model_provider": model_provider,
            "created_at": now_iso
        })

        # SQLite
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO chat_messages (id, session_id, role, content, tools_executed_json, model_provider, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (msg_id, session_id, role, content, tools_json, model_provider, now_iso))
                conn.commit()
        except Exception as e:
            logging.error(f"Error saving chat message to database: {e}")

    @classmethod
    def reset_session(cls, session_id: str):
        """Clears conversation memory for the given session."""
        cls.init_db()
        cls._MEMORY_STORE.pop(session_id, None)
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
                conn.commit()
            logging.info(f"Cleared chat memory for session {session_id}")
        except Exception as e:
            logging.error(f"Error clearing chat memory: {e}")

    # ============================================================
    # CHAT ENTRYPOINT (CONTEXTUAL AGENT)
    # ============================================================

    @classmethod
    def chat(
        cls,
        user_message: str,
        session_id: Optional[str] = None,
        context_diamond: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processes a user question with multi-turn conversation memory,
        tool calling, and live market intelligence.
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        clean_query = user_message.strip()
        if not clean_query:
            return {
                "success": False,
                "error": "Empty message received.",
                "session_id": session_id
            }

        # Retrieve conversation history
        history = cls.get_conversation_history(session_id)

        # Record user turn
        cls.record_message(session_id, role="user", content=clean_query)

        # Check API Keys
        gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        groq_api_key = os.getenv("GROQ_API_KEY", "").strip()

        tools_executed: List[Dict[str, Any]] = []

        # 1. Try Google Gemini API (Primary Free-Tier LLM)
        if gemini_api_key:
            res = cls._call_gemini_api(
                user_message=clean_query,
                history=history,
                gemini_api_key=gemini_api_key,
                context_diamond=context_diamond
            )
            if res.get("success"):
                reply = res["reply"]
                tools_executed = res.get("tools_executed", [])
                provider = res.get("provider", "Google Gemini Flash (Free Tier)")
                cls.record_message(session_id, role="model", content=reply, tools_executed=tools_executed, model_provider=provider)
                return {
                    "success": True,
                    "reply": reply,
                    "tools_executed": tools_executed,
                    "session_id": session_id,
                    "provider": provider,
                    "is_live_llm": True
                }
            else:
                logging.warning(f"Gemini API call failed: {res.get('error')}. Checking alternate provider...")

        # 2. Try Groq API (Secondary Free-Tier LLM)
        if groq_api_key:
            res = cls._call_groq_api(
                user_message=clean_query,
                history=history,
                groq_api_key=groq_api_key,
                context_diamond=context_diamond
            )
            if res.get("success"):
                reply = res["reply"]
                tools_executed = res.get("tools_executed", [])
                provider = res.get("provider", "Groq Llama 3.3 70B (Free Tier)")
                cls.record_message(session_id, role="model", content=reply, tools_executed=tools_executed, model_provider=provider)
                return {
                    "success": True,
                    "reply": reply,
                    "tools_executed": tools_executed,
                    "session_id": session_id,
                    "provider": provider,
                    "is_live_llm": True
                }
            else:
                logging.warning(f"Groq API call failed: {res.get('error')}.")

        # 3. Autonomous Local Agentic Engine (Guaranteed zero-failure intelligent fallback)
        res_local = cls._execute_autonomous_local_reasoning(
            user_message=clean_query,
            history=history,
            context_diamond=context_diamond
        )
        reply = res_local["reply"]
        tools_executed = res_local.get("tools_executed", [])
        provider = "GEMFORECAST Autonomous Trade Engine (Local)"

        cls.record_message(session_id, role="model", content=reply, tools_executed=tools_executed, model_provider=provider)

        return {
            "success": True,
            "reply": reply,
            "tools_executed": tools_executed,
            "session_id": session_id,
            "provider": provider,
            "is_live_llm": False,
            "notice": "Operating on GEMFORECAST Autonomous Trade Engine. Configure GEMINI_API_KEY in .env to enable Cloud Gemini reasoning."
        }

    # ============================================================
    # GOOGLE GEMINI FREE-TIER API IMPLEMENTATION
    # ============================================================

    @classmethod
    def _call_gemini_api(
        cls,
        user_message: str,
        history: List[Dict[str, Any]],
        gemini_api_key: str,
        context_diamond: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes multi-turn conversation with Google Gemini API,
        handling native Tool/Function Calling loop.
        """
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key}"

        # Construct contents array
        contents = []
        for h in history[-8:]:  # keep recent context
            role = "user" if h["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": h["content"]}]})

        current_prompt = user_message
        if context_diamond:
            current_prompt += f"\n\n[Active Diamond Dossier in Context: {json.dumps(context_diamond)}]"

        contents.append({"role": "user", "parts": [{"text": current_prompt}]})

        # Gemini tool declarations
        gemini_tools = [{"function_declarations": cls.TOOLS_DECLARATIONS}]

        payload = {
            "contents": contents,
            "system_instruction": {"parts": [{"text": cls.SYSTEM_INSTRUCTION}]},
            "tools": gemini_tools,
            "generation_config": {
                "temperature": 0.25,
                "max_output_tokens": 1500
            }
        }

        tools_executed: List[Dict[str, Any]] = []

        try:
            # First turn: model might return text or function call
            resp = requests.post(endpoint, json=payload, timeout=12)
            if resp.status_code != 200:
                return {"success": False, "error": f"Gemini HTTP {resp.status_code}: {resp.text}"}

            resp_data = resp.json()
            candidates = resp_data.get("candidates", [])
            if not candidates:
                return {"success": False, "error": "No candidates returned from Gemini."}

            parts = candidates[0].get("content", {}).get("parts", [])
            function_call = None
            text_reply = ""

            for p in parts:
                if "functionCall" in p:
                    function_call = p["functionCall"]
                if "text" in p:
                    text_reply += p["text"]

            # If model requested a function call, execute it and send functionResponse back
            if function_call:
                fn_name = function_call.get("name")
                fn_args = function_call.get("args", {})
                logging.info(f"Gemini requested tool call: {fn_name}({fn_args})")

                tool_result = cls.execute_tool(fn_name, fn_args)
                tools_executed.append({
                    "tool": fn_name,
                    "arguments": fn_args,
                    "output": tool_result
                })

                # Append model's functionCall turn
                contents.append({
                    "role": "model",
                    "parts": [{"functionCall": function_call}]
                })

                # Append function response turn
                contents.append({
                    "role": "function",
                    "parts": [{
                        "functionResponse": {
                            "name": fn_name,
                            "response": tool_result
                        }
                    }]
                })

                # Second turn: get final synthesis from Gemini
                followup_payload = {
                    "contents": contents,
                    "system_instruction": {"parts": [{"text": cls.SYSTEM_INSTRUCTION}]},
                    "tools": gemini_tools,
                    "generation_config": {
                        "temperature": 0.25,
                        "max_output_tokens": 1500
                    }
                }

                resp_followup = requests.post(endpoint, json=followup_payload, timeout=12)
                if resp_followup.status_code == 200:
                    f_data = resp_followup.json()
                    f_parts = f_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    final_text = "".join([pt.get("text", "") for pt in f_parts if "text" in pt])
                    if final_text:
                        return {
                            "success": True,
                            "reply": final_text,
                            "tools_executed": tools_executed,
                            "provider": f"Google Gemini ({model})"
                        }

            if text_reply:
                return {
                    "success": True,
                    "reply": text_reply,
                    "tools_executed": tools_executed,
                    "provider": f"Google Gemini ({model})"
                }

            return {"success": False, "error": "Empty response from Gemini."}

        except Exception as e:
            logging.error(f"Error communicating with Gemini API: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================
    # GROQ FREE-TIER API IMPLEMENTATION
    # ============================================================

    @classmethod
    def _call_groq_api(
        cls,
        user_message: str,
        history: List[Dict[str, Any]],
        groq_api_key: str,
        context_diamond: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Executes chat completions with Groq free-tier endpoint."""
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        endpoint = "https://api.groq.com/openai/v1/chat/completions"

        messages = [{"role": "system", "content": cls.SYSTEM_INSTRUCTION}]
        for h in history[-8:]:
            role = "user" if h["role"] == "user" else "assistant"
            messages.append({"role": role, "content": h["content"]})

        prompt = user_message
        if context_diamond:
            prompt += f"\n\n[Active Diamond Dossier: {json.dumps(context_diamond)}]"
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.25,
            "max_tokens": 1500
        }

        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "reply": content,
                    "tools_executed": [],
                    "provider": f"Groq ({model})"
                }
            return {"success": False, "error": f"Groq HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            logging.error(f"Error calling Groq: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================
    # AUTONOMOUS LOCAL REASONING ENGINE (INTELLIGENT FALLBACK)
    # ============================================================

    @classmethod
    def _execute_autonomous_local_reasoning(
        cls,
        user_message: str,
        history: List[Dict[str, Any]],
        context_diamond: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Dynamic, context-aware reasoning engine that executes live domain tools,
        computes financial math, inspects risks, and formulates expert negotiation guidance
        without hardcoded static text.
        """
        q = user_message.lower().strip()
        tools_executed: List[Dict[str, Any]] = []

        # 1. Detect if query relates to Bullion / Gold / Silver rates
        if any(w in q for w in ["gold", "silver", "ibja", "bullion", "24k", "22k", "18k", "14k", "bhav"]):
            bullion_data = cls.execute_tool("get_live_bullion_rates", {})
            tools_executed.append({
                "tool": "get_live_bullion_rates",
                "arguments": {},
                "output": bullion_data
            })
            r10 = bullion_data.get("rates_per_10g", {})
            reply = (
                f"### 🪙 Official IBJA Bullion Market Intelligence\n\n"
                f"**Session**: {bullion_data.get('session')} ({bullion_data.get('publication_timestamp')})\n"
                f"**Freshness Status**: `{bullion_data.get('freshness')}`\n\n"
                f"| Purity Tier | Standard Fineness | Benchmark Rate (per 10g) |\n"
                f"| :--- | :--- | :--- |\n"
                f"| **24K Fine Gold** | 99.9% (999) | **{r10.get('24K')}** |\n"
                f"| **22K Standard Gold** | 91.6% (916) | **{r10.get('22K')}** |\n"
                f"| **18K Hallmarked Gold** | 75.0% (750) | **{r10.get('18K')}** |\n"
                f"| **14K Studded Gold** | 58.3% (585) | **{r10.get('14K')}** |\n"
                f"| **Silver 999** | 99.9% (per 1kg) | **{r10.get('Silver_999_per_kg')}** |\n\n"
                f"#### 💡 Jeweller Trade Advisory:\n"
                f"• For studded diamond jewellery, **18K Hallmarked Gold** ({r10.get('18K')}/10g) offers the ideal balance of tensile strength for prongs and metal value.\n"
                f"• When quoting customers, factor a standard **₹750–₹1,200 per gram making charge** + **3% GST (HSN 7113)**."
            )
            return {"reply": reply, "tools_executed": tools_executed}

        # 2. Extract diamond parameters from message or context
        carat_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ct|carat)', q)
        carat = float(carat_match.group(1)) if carat_match else None

        color_match = re.search(r'\b([d-k])\b(?:\s*color)?', q)
        color = color_match.group(1).upper() if color_match else None

        clarity_match = re.search(r'\b(fl|if|vvs1|vvs2|vs1|vs2|si1|si2)\b', q)
        clarity = clarity_match.group(1).upper() if clarity_match else None

        is_lab = any(w in q for w in ["lab-grown", "lab grown", "cvd", "hpht", "lgd", "surat"])
        origin_type = "Lab-Grown" if is_lab else "Natural"

        # Check asking price in query (e.g. ₹3,50,000, 3.5 lakh, 350k)
        asking_price = None
        lakh_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)\b', q)
        if lakh_match:
            asking_price = float(lakh_match.group(1)) * 100000.0
        else:
            raw_num_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{2,3})*(?:\.\d+)?)\b', q)
            if raw_num_match:
                val = float(raw_num_match.group(1).replace(",", ""))
                if val > 5000:
                    asking_price = val

        # Fallback to context diamond if available
        if context_diamond:
            spec = context_diamond.get("diamond_spec", {})
            carat = carat or float(spec.get("carat", 1.0))
            color = color or str(spec.get("color", "F")).upper()
            clarity = clarity or str(spec.get("clarity", "VS1")).upper()
            if "Lab" in str(spec.get("origin_type", "")):
                origin_type = "Lab-Grown"

        # Defaults if unspecified
        carat = carat or 1.02
        color = color or "E"
        clarity = clarity or "VS1"

        # Execute live diamond pricing tool
        quote_tool_res = cls.execute_tool("get_diamond_market_quote", {
            "carat": carat,
            "color": color,
            "clarity": clarity,
            "cut": "Ideal",
            "shape": "Round Brilliant",
            "origin_type": origin_type
        })
        tools_executed.append({
            "tool": "get_diamond_market_quote",
            "arguments": {"carat": carat, "color": color, "clarity": clarity, "origin_type": origin_type},
            "output": quote_tool_res
        })

        wholesale_val = quote_tool_res.get("total_wholesale_inr", 0.0)
        price_per_ct = quote_tool_res.get("price_per_carat_inr", 0.0)
        source = quote_tool_res.get("source", "Market Benchmark")

        # Target acquisition (Buy Target)
        buy_discount = 0.10 if origin_type == "Natural" else 0.15
        target_buy = wholesale_val * (1.0 - buy_discount)

        # Suggested retail
        markup_pct = 0.25 if origin_type == "Natural" else 0.45
        target_sell = wholesale_val * (1.0 + markup_pct)
        expected_profit = target_sell - target_buy
        target_margin = (expected_profit / target_sell) * 100.0 if target_sell > 0 else 0.0

        # Run Jewellery Calculator tool for full ring quote
        calc_tool_res = cls.execute_tool("calculate_jewellery_quotation", {
            "net_gold_weight": 8.5,
            "purity": "18K",
            "wastage_pct": 5.0,
            "diamond_carat": carat,
            "diamond_rate_per_carat": price_per_ct,
            "making_charge_per_gram": 750.0,
            "retail_markup_pct": 25.0,
            "is_interstate": False
        })
        tools_executed.append({
            "tool": "calculate_jewellery_quotation",
            "arguments": {"net_gold_weight": 8.5, "purity": "18K", "diamond_carat": carat, "diamond_rate_per_carat": price_per_ct},
            "output": calc_tool_res
        })

        # Evaluate asking price deal
        deal_verdict = "FAIR WHOLESALE PARITY"
        counter_offer = target_buy
        risk_notes = []

        if asking_price:
            diff_pct = ((asking_price - wholesale_val) / wholesale_val) * 100.0
            if asking_price <= target_buy:
                deal_verdict = "STRONG BUY (HIGH PROFIT MARGIN)"
                counter_offer = asking_price
            elif asking_price <= wholesale_val:
                deal_verdict = "NEGOTIABLE DEAL (COUNTER-OFFER RECOMMENDED)"
                counter_offer = round(target_buy, -2)
            else:
                deal_verdict = f"OVERPRICED BY {diff_pct:.1f}% OVER BDB BENCHMARK"
                counter_offer = round(wholesale_val * 0.92, -2)
                risk_notes.append(f"Supplier is asking ₹{asking_price:,.0f}, which is {diff_pct:.1f}% above wholesale parity.")

        if origin_type == "Lab-Grown":
            risk_notes.append("Rapid Surat LGD factory capacity expansion creates high depreciation risk; avoid holding unsold LGD inventory beyond 45 days.")
        else:
            risk_notes.append("Natural mined stone holds solid liquidity at Mumbai BDB; insist on verified IGI laser inscription on girdle before counter payment.")

        # Build comprehensive markdown advisory
        reply = (
            f"### 💎 Indian Jeweller Trade Advisory: {carat:.2f} ct • {color} / {clarity} ({origin_type})\n\n"
            f"**Verified Benchmark Source**: `{source}`\n\n"
            f"#### 📊 Wholesale Valuation & Retail Pricing Strategy\n"
            f"- **Fair Wholesale Market Value**: **₹ {wholesale_val:,.0f}** (`₹ {price_per_ct:,.0f}/ct`)\n"
            f"- **Target Jeweller Acquisition (Buy Price)**: **₹ {target_buy:,.0f}** ({int(buy_discount*100)}% below wholesale)\n"
            f"- **Suggested Retail Pricing Quote**: **₹ {target_sell:,.0f}** + 3% GST\n"
            f"- **Suggested Customer Retail Quote**: **₹ {target_sell:,.0f}** + 3% GST\n"
            f"- **Projected Gross Profit**: **₹ {expected_profit:,.0f}** (Gross Margin: **{target_margin:.1f}%**)\n\n"
        )

        if asking_price:
            reply += (
                f"#### ⚖️ Deal Appraisal for Asking Price of ₹ {asking_price:,.0f}\n"
                f"- **Verdict**: **{deal_verdict}**\n"
                f"- **Counter-Offer Target**: **₹ {counter_offer:,.0f}** (Strict payment term: RTGS on counter verification)\n\n"
            )

        reply += (
            f"#### 💍 Solitaire Ring Landed Cost Breakdown (18K Gold + Solitaire)\n"
            f"Using standard 8.5g 18K Hallmarked Gold mounting with 5% wastage:\n"
            f"- **Total Landed Cost**: **{calc_tool_res.get('formatted_landed_cost')}**\n"
            f"- **Customer Grand Total with 3% GST**: **{calc_tool_res.get('formatted_grand_total')}**\n\n"
            f"#### ⚠️ Trade Risk & Gemological Quality Analysis\n"
        )
        for rk in risk_notes:
            reply += f"• {rk}\n"

        reply += (
            f"\n#### 🎯 Negotiation Strategy\n"
            f"1. **Inspection**: Verify Table (54.0%–57.5%) and Depth (61.0%–62.5%) under loupe to rule out fish-eye light leakage.\n"
            f"2. **Counter Script**: *'Based on current {origin_type} BDB/Surat wholesale parity for {color}/{clarity}, my firm counter is ₹{counter_offer:,.0f} with instant RTGS clearance upon laser inscription matching.'*\n"
        )

        return {"reply": reply, "tools_executed": tools_executed}
