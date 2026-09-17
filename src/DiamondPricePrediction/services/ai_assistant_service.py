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
    def ask_assistant(cls, query: str, context_diamond: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Answers practical jeweller business, pricing, and negotiation questions in Indian trade context."""
        q = query.lower().strip()
        response_title = "Indian Jeweller AI Trade Advisory"

        # 1. Buying / Negotiation advice at a specific price (e.g. "Can I buy at ₹X?", "Supplier is asking ₹X")
        price_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakh|k)?', q)
        if any(w in q for w in ["buy at", "supplier asking", "can i buy", "what should i pay", "counter offer", "negotiate"]):
            response_text = (
                "**Indian Wholesale Negotiation & Buying Guidelines:**\n\n"
                "• **Bharat Diamond Bourse (BDB) Wholesale Rule:** Always target acquiring at **8% to 12% below the fair wholesale market benchmark** for Natural stones, and **15% below** for Lab-Grown (LGD) to ensure safety against market fluctuations.\n"
                "• **Payment Terms:** If purchasing in full cash/instant RTGS on Surat/Mumbai counters, insist on an additional **1.5% to 2.0% cash discount**.\n"
                "• **Memo Verification:** Always verify the IGI laser inscription on the girdle under 20x loupe against the official IGI digital certificate before releasing payment.\n"
                "• **GST Impact:** Add 3% GST on polished diamonds when factoring input tax credit (ITC)."
            )
            tags = ["Negotiation Tactics", "BDB Trading", "Cash Discount", "GST 3%"]

        # 2. What should I ask the customer? (Retail asking price & margins)
        elif any(w in q for w in ["what should i ask", "customer price", "retail price", "how much to sell", "markup"]):
            response_text = (
                "**Retail Pricing & Customer Quote Formula:**\n\n"
                "• **Solitaire Rings (Natural):** Apply a **20% to 30% gross markup** over your wholesale landed cost. For instance, a ₹4,00,000 wholesale stone should retail between **₹4,80,000 and ₹5,20,000 + 3% GST**.\n"
                "• **Lab-Grown Solitaires:** Apply a **40% to 60% gross markup** since base per-carat prices are lower (₹15k-₹28k/ct), allowing healthy absolute profit while remaining attractive to young buyers.\n"
                "• **Jewellery Making Charges:** Standard 18K/14K hallmarked gold mountings typically charge **₹850 to ₹1,400 per gram** making charge + casting losses."
            )
            tags = ["Retail Asking Price", "Markup Strategy", "Making Charges", "Solitaire Rings"]

        # 3. Lab-Grown vs Natural Dynamics in India
        elif any(w in q for w in ["lab-grown", "lab grown", "cvd", "hpht", "natural vs lab", "surat"]):
            response_text = (
                "**Indian Market: Natural vs. Lab-Grown (LGD) Trade Dynamics:**\n\n"
                "• **Natural Diamonds (BDB Mumbai):** Backed by geological scarcity and long-term resale liquidity. Preferred for traditional Indian bridal jewellery and high-value family heirlooms.\n"
                "• **Lab-Grown Diamonds (Surat SDB):** Rapidly expanding in urban metros (Delhi, Mumbai, Bengaluru) for fashion and budget-conscious engagement rings. Trades at an **85% to 92% wholesale discount** compared to Natural.\n"
                "• **Trade Advice:** Maintain separate inventory showcases. Clearly state IGI Lab-Grown certification to ensure 100% customer trust and BIS compliance."
            )
            tags = ["Natural vs LGD", "Surat Hub", "Bridal Solitaires", "Customer Trust"]

        # 4. Fluorescence Trade Impact in India
        elif any(w in q for w in ["fluorescence", "blue", "medium blue", "strong blue", "milky"]):
            response_text = (
                "**Fluorescence Discount Matrix in Indian Trade:**\n\n"
                "• **On D–F (Colorless) Diamonds:** Strong Blue fluorescence carries an **8% to 12% wholesale discount** in Mumbai/Surat markets due to consumer preference for zero haze in bright daylight.\n"
                "• **On I–K (Near-Colorless/Warm) Diamonds:** Medium to Strong Blue fluorescence actually cancels yellow tint and makes the stone look **1 to 2 color shades whiter** face-up without penalty.\n"
                "• **Trade Tip:** Always inspect under 365nm UV lamp and natural sunlight before finalizing wholesale purchases."
            )
            tags = ["Fluorescence", "Colorless Discount", "UV Inspection"]

        # 5. Which diamond is better? (Comparison query)
        elif any(w in q for w in ["which is better", "compare", "better buy", "difference"]):
            response_text = (
                "**Diamond Decision Framework for Jewellers:**\n\n"
                "• **For Investment / High Resale Value:** Prioritize Natural Mined, Triple Excellent (3EX), D-F Color, VVS clarity with IGI certificate and None fluorescence.\n"
                "• **For Maximum Visual Size at Best Value:** Choose G-H Color, VS2 Clarity (100% eye-clean) with Ideal Cut. The cut quality masks the slight color drop while saving 25-35% in cost.\n"
                "• **For Budget Luxury / High Jeweller Margin:** Choose IGI Lab-Grown (CVD) D-E VVS2. Retail with 45%+ gross margin."
            )
            tags = ["Comparison Logic", "Quality vs Value", "Resale Liquidity"]

        # Default General Jeweller Intelligence
        else:
            response_text = (
                f"**Gemological Trade Advisory for '{query}':**\n\n"
                "In the Indian jewellery trade, accurate diamond appraisal requires cross-examining the **IGI Certificate Number**, verified proportions (Table 54-57.5%, Depth 61-62.5%), and current Mumbai BDB / Surat wholesale price benchmarks.\n\n"
                "• **Recommendation:** Check the IGI Report Number in the platform's appraisal portal to generate instant Suggested Buy, Suggested Sell, and Expected Jeweller Profit in Indian Rupees (₹)."
            )
            tags = ["IGI Verification", "Indian Wholesale", "Jeweller Decisions"]

        return {
            "title": response_title,
            "answer": response_text,
            "tags": tags,
            "context_attached": bool(context_diamond)
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
