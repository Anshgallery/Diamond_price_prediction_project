import re
from typing import Dict, Any, List, Optional
from DiamondPricePrediction.services.indian_market_service import IndianMarketService

class AIAssistantService:
    """
    India-First Jeweller AI Advisory, Proportions Analyzer & Multi-Report Recommendation Engine.
    
    Provides gemological reasoning, Tolkowsky cut validation, negotiation guidance,
    and automated 5-Report competitive comparison awards.
    """

    COLOR_ORDER = {"D": 7, "E": 6, "F": 5, "G": 4, "H": 3, "I": 2, "J": 1}
    CLARITY_ORDER = {"FL": 9, "IF": 8, "VVS1": 7, "VVS2": 6, "VS1": 5, "VS2": 4, "SI1": 3, "SI2": 2, "I1": 1}
    CUT_ORDER = {"Ideal": 5, "Excellent": 5, "Very Good": 4, "Good": 3, "Fair": 2, "Poor": 1}

    @classmethod
    def evaluate_proportions(
        cls,
        shape: str,
        table: float,
        depth: float,
        x: float,
        y: float,
        z: float
    ) -> Dict[str, Any]:
        """Evaluates physical diamond proportions against Tolkowsky Ideal & IGI standards."""
        evaluations = []
        overall_score = 100

        ratio = None
        if x > 0 and y > 0:
            ratio = round(max(x, y) / min(x, y), 2)

        # 1. Table Percentage
        if 54.0 <= table <= 57.5:
            evaluations.append({
                "metric": "Table Size",
                "value": f"{table:.1f}%",
                "grade": "Tolkowsky Ideal (54-57.5%)",
                "status": "Optimal",
                "comment": "Exceptional optical balance of brilliance (white light) and fire (dispersion)."
            })
        elif 53.0 <= table <= 59.0:
            evaluations.append({
                "metric": "Table Size",
                "value": f"{table:.1f}%",
                "grade": "Excellent Range (53-59%)",
                "status": "Very Good",
                "comment": "Good commercial brilliance with minimal light leakage."
            })
            overall_score -= 5
        elif table > 62.0:
            evaluations.append({
                "metric": "Table Size",
                "value": f"{table:.1f}%",
                "grade": "Over-spread (> 62%)",
                "status": "Light Leakage Risk",
                "comment": "Excessive table size creates fish-eye reflection and dampens colored fire."
            })
            overall_score -= 20
        else:
            evaluations.append({
                "metric": "Table Size",
                "value": f"{table:.1f}%",
                "grade": "Small Table (< 53%)",
                "status": "Deep Crown",
                "comment": "High fire dispersion but reduced face-up spread."
            })
            overall_score -= 10

        # 2. Total Depth Percentage
        if 61.0 <= depth <= 62.5:
            evaluations.append({
                "metric": "Total Depth",
                "value": f"{depth:.1f}%",
                "grade": "Ideal Depth (61.0-62.5%)",
                "status": "Optimal",
                "comment": "Maximizes total internal reflection with zero pavilion light leakage."
            })
        elif 59.5 <= depth <= 63.5:
            evaluations.append({
                "metric": "Total Depth",
                "value": f"{depth:.1f}%",
                "grade": "Excellent Range (59.5-63.5%)",
                "status": "Very Good",
                "comment": "Standard trade tolerance for round brilliant diamonds."
            })
            overall_score -= 5
        elif depth > 64.0:
            evaluations.append({
                "metric": "Total Depth",
                "value": f"{depth:.1f}%",
                "grade": "Too Deep (> 64%)",
                "status": "Nail-head Risk",
                "comment": "Hides carat weight in pavilion; face-up size appears smaller than carat weight."
            })
            overall_score -= 25
        else:
            evaluations.append({
                "metric": "Total Depth",
                "value": f"{depth:.1f}%",
                "grade": "Shallow Cut (< 59%)",
                "status": "Fish-eye Risk",
                "comment": "Light escapes through base, producing a dull grey central ring."
            })
            overall_score -= 20

        # 3. L/W Ratio
        if ratio:
            if ratio <= 1.02:
                evaluations.append({
                    "metric": "Length-to-Width Ratio",
                    "value": f"{ratio:.2f}",
                    "grade": "Near-Perfect Circularity (1.00-1.02)",
                    "status": "Optimal",
                    "comment": "Excellent round symmetry."
                })
            else:
                evaluations.append({
                    "metric": "Length-to-Width Ratio",
                    "value": f"{ratio:.2f}",
                    "grade": f"Out-of-Round ({ratio:.2f})",
                    "status": "Sub-optimal",
                    "comment": "Visible deviation from circular symmetry."
                })
                overall_score -= 10

        overall_score = max(30, min(100, overall_score))

        return {
            "shape": shape,
            "overall_proportion_score": overall_score,
            "grade_label": "Super-Ideal Cut" if overall_score >= 95 else ("Ideal Proportions" if overall_score >= 85 else "Standard Commercial"),
            "evaluations": evaluations,
            "ratio": ratio
        }

    @classmethod
    def ask_assistant(cls, query: str, context_diamond: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Answers practical jeweller business, pricing, and negotiation questions in Indian trade context
        using the real LLM-powered AITradeAdvisorAgent with live tool calling and conversation memory.
        """
        from DiamondPricePrediction.services.ai_trade_advisor_agent import AITradeAdvisorAgent

        chat_res = AITradeAdvisorAgent.chat(
            user_message=query,
            session_id=session_id,
            context_diamond=context_diamond
        )

        reply_text = chat_res.get("reply", "")
        tools_used = chat_res.get("tools_executed", [])
        tags = [t.get("tool", "Trade Analysis") for t in tools_used]
        if not tags:
            tags = ["BDB Benchmark", "Trade Advisory", "Risk Assessment"]

        return {
            "title": "Indian Jeweller AI Trade Advisory",
            "answer": reply_text,
            "tags": tags,
            "context_attached": bool(context_diamond),
            "tools_executed": tools_used,
            "session_id": chat_res.get("session_id"),
            "provider": chat_res.get("provider", "Local Engine"),
            "is_live_llm": chat_res.get("is_live_llm", False)
        }

    @classmethod
    def compare_5_reports(cls, diamond_dossiers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesizes up to 5 IGI diamond dossiers and generates competitive trade rankings
        and specialized AI awards:
          - Overall Jeweller Pick
          - Best Quality
          - Best Value for Money
          - Best Buy (Highest Profit Margin)
          - Best Resale / Liquidity
        """
        if not diamond_dossiers or len(diamond_dossiers) < 2:
            return {
                "error": "At least 2 diamond dossiers required for comparison.",
                "awards": {},
                "comparison_matrix": [],
                "executive_summary": "Insufficient diamond dossiers for multi-report comparison."
            }

        scored_diamonds = []
        for idx, d in enumerate(diamond_dossiers):
            spec = d.get("diamond_spec", {})
            val = d.get("valuation", {})

            carat = float(spec.get("carat", 1.0))
            color = str(spec.get("color", "F")).upper()
            clarity = str(spec.get("clarity", "VS1")).upper()
            cut = str(spec.get("cut", "Ideal")).title()
            is_lab = "Lab" in str(spec.get("origin_type", "Natural"))
            
            fair_market = float(val.get("fair_market_value", 0))
            suggested_buy = float(val.get("suggested_buy_price", 0))
            suggested_sell = float(val.get("suggested_sell_price", 0))
            profit = float(val.get("expected_profit", suggested_sell - suggested_buy))
            margin_pct = float(val.get("expected_margin_pct", 25.0))
            quality_score = int(val.get("quality_score", 75))

            # Quality index score
            color_rank = cls.COLOR_ORDER.get(color, 4)
            clarity_rank = cls.CLARITY_ORDER.get(clarity, 4)
            cut_rank = cls.CUT_ORDER.get(cut, 4)
            quality_index = (color_rank * 3) + (clarity_rank * 3.5) + (cut_rank * 3) + (10 if not is_lab else 0)

            # AI Face / Style-Value Layer Extraction
            style_analysis = val.get("style_value_analysis", {})
            ai_face_label = style_analysis.get("ai_face_label", val.get("ai_face_label", "Moderate Commercial Tier"))
            ai_face_tier = style_analysis.get("ai_face_tier", val.get("ai_face_tier", "moderate"))
            ai_face_badge = style_analysis.get("ai_face_badge_class", "badge-emerald")

            # Value for money: quality score relative to per-carat price
            ppc = fair_market / max(carat, 0.01)
            value_ratio = round((quality_score * 1000) / max(ppc, 1000), 2)

            scored_diamonds.append({
                "index": idx,
                "report_number": spec.get("report_number", f"Report #{idx+1}"),
                "shape": spec.get("shape", "Round Brilliant"),
                "carat": carat,
                "color": color,
                "clarity": clarity,
                "cut": cut,
                "origin_type": "Lab-Grown" if is_lab else "Natural",
                "ai_face_tier": ai_face_tier,
                "ai_face_label": ai_face_label,
                "ai_face_badge": ai_face_badge,
                "pricing_preference_signal": val.get("pricing_preference_signal", ai_face_tier),
                "fair_market_inr": fair_market,
                "fair_market_formatted": IndianMarketService.format_inr(fair_market),
                "suggested_buy_inr": suggested_buy,
                "suggested_buy_formatted": IndianMarketService.format_inr(suggested_buy),
                "suggested_sell_inr": suggested_sell,
                "suggested_sell_formatted": IndianMarketService.format_inr(suggested_sell),
                "profit_inr": profit,
                "profit_formatted": IndianMarketService.format_inr(profit),
                "margin_pct": margin_pct,
                "quality_score": quality_score,
                "quality_index": quality_index,
                "value_ratio": value_ratio,
                "ppc": ppc,
                "spec": spec,
                "val": val
            })

        # 1. Best Quality (Highest 4Cs + Polish/Symmetry score)
        best_quality = max(scored_diamonds, key=lambda x: (x["quality_score"], x["carat"]))

        # 2. Best Buy / Highest Profit (Maximum absolute jeweller profit in ₹)
        best_buy = max(scored_diamonds, key=lambda x: (x["profit_inr"], x["margin_pct"]))

        # 3. Best Value for Money (Best Quality per Rupee spent)
        best_value = max(scored_diamonds, key=lambda x: x["value_ratio"])

        # 4. Best Resale / Liquidity (Natural, standard magic size, popular color/clarity)
        natural_stones = [s for s in scored_diamonds if s["origin_type"] == "Natural"]
        if natural_stones:
            best_resale = max(natural_stones, key=lambda x: (x["carat"] >= 1.0, x["color"] in ["D", "E", "F"], x["quality_score"]))
        else:
            best_resale = max(scored_diamonds, key=lambda x: (x["color"] in ["D", "E"], x["quality_score"]))

        # 5. Overall Pick (Balanced highest composite score)
        def overall_score(d):
            return (d["quality_score"] * 0.35) + (d["margin_pct"] * 0.35) + (d["value_ratio"] * 0.30)

        overall_pick = max(scored_diamonds, key=overall_score)

        awards = {
            "overall_pick": {
                "title": "Overall Jeweller Pick",
                "badge": "🏆 TOP RECOMMENDATION",
                "diamond": overall_pick,
                "rationale": f"Optimal balance of premium optical quality ({overall_pick['color']}/{overall_pick['clarity']}), strong Indian market liquidity, and {overall_pick['profit_formatted']} expected gross profit."
            },
            "best_quality": {
                "title": "Best Gemological Quality",
                "badge": "💎 TOP GEM GRADE",
                "diamond": best_quality,
                "rationale": f"Highest physical and optical grading in comparison matrix ({best_quality['carat']:.2f} ct, {best_quality['color']} color, {best_quality['clarity']} clarity with {best_quality['quality_score']}/100 quality rating)."
            },
            "best_value": {
                "title": "Best Value for Money",
                "badge": "💰 MAXIMUM VALUE",
                "diamond": best_value,
                "rationale": f"Highest visual sparkle and 4Cs prestige per Rupee invested ({best_value['fair_market_formatted']} wholesale value)."
            },
            "best_buy": {
                "title": "Best Jeweller Profit (Highest ROI)",
                "badge": "🎯 HIGHEST MARGIN",
                "diamond": best_buy,
                "rationale": f"Yields the highest absolute profit for the jeweller ({best_buy['profit_formatted']} profit with {best_buy['margin_pct']:.1f}% margin)."
            },
            "best_resale": {
                "title": "Best Resale & Trade Liquidity",
                "badge": "🔄 FAST LIQUIDITY",
                "diamond": best_resale,
                "rationale": f"Most liquid specification in Indian wholesale trading with rapid turnaround in Zaveri Bazaar / Surat counters."
            }
        }

        exec_summary = (
            f"Evaluated {len(scored_diamonds)} IGI-certified diamonds. "
            f"The **Overall Jeweller Pick** is **{overall_pick['report_number']}** ({overall_pick['carat']:.2f} ct {overall_pick['color']}/{overall_pick['clarity']}), "
            f"delivering an estimated **{overall_pick['profit_formatted']}** gross profit at a suggested customer asking price of **{overall_pick['suggested_sell_formatted']}**."
        )

        return {
            "comparison_matrix": scored_diamonds,
            "awards": awards,
            "executive_summary": exec_summary,
            "total_evaluated": len(scored_diamonds)
        }
