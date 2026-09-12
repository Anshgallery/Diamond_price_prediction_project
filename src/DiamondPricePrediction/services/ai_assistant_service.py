import re
from typing import Dict, Any, List

class AIAssistantService:
    """
    Jeweller Domain-Aware AI Assistant & Diamond Proportion Analyzer.
    Provides expert gemological reasoning, Tolkowsky ideal cut validation,
    pricing curve explanations, and trade market insights.
    """

    TOLKOWSKY_STANDARDS = {
        "Round Brilliant": {
            "ideal_table_min": 54.0,
            "ideal_table_max": 57.0,
            "ideal_depth_min": 61.0,
            "ideal_depth_max": 62.5,
            "ideal_ratio_min": 1.00,
            "ideal_ratio_max": 1.02
        }
    }

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
        """
        Evaluates physical diamond proportions against GIA Excellent & Tolkowsky Ideal standards.
        """
        evaluations = []
        overall_score = 100

        # Calculate Length-to-Width Ratio
        ratio = None
        if x > 0 and y > 0:
            ratio = round(max(x, y) / min(x, y), 2)

        # 1. Table Percentage Analysis
        if 54.0 <= table <= 57.0:
            evaluations.append({
                "metric": "Table Size",
                "value": f"{table:.1f}%",
                "grade": "Tolkowsky Ideal (54-57%)",
                "status": "Optimal",
                "comment": "Exceptional optical balance between brilliance (white light) and fire (colored dispersion)."
            })
        elif 53.0 <= table <= 59.0:
            evaluations.append({
                "metric": "Table Size",
                "value": f"{table:.1f}%",
                "grade": "GIA Excellent Range (53-59%)",
                "status": "Very Good",
                "comment": "Good light performance with standard commercial brilliance."
            })
            overall_score -= 5
        elif table > 62.0:
            evaluations.append({
                "metric": "Table Size",
                "value": f"{table:.1f}%",
                "grade": "Over-spread (> 62%)",
                "status": "Light Leakage Risk",
                "comment": "Large table creates 'fish-eye' effect and diminishes rainbow fire dispersion."
            })
            overall_score -= 20
        else:
            evaluations.append({
                "metric": "Table Size",
                "value": f"{table:.1f}%",
                "grade": "Small Table (< 53%)",
                "status": "Fair / Deep Crown",
                "comment": "High fire but reduced apparent spread and total white light return."
            })
            overall_score -= 10

        # 2. Depth Percentage Analysis
        if 61.0 <= depth <= 62.5:
            evaluations.append({
                "metric": "Total Depth",
                "value": f"{depth:.1f}%",
                "grade": "Ideal Depth (61.0-62.5%)",
                "status": "Optimal",
                "comment": "Maximizes total internal reflection with zero bottom light leakage."
            })
        elif 59.5 <= depth <= 63.5:
            evaluations.append({
                "metric": "Total Depth",
                "value": f"{depth:.1f}%",
                "grade": "GIA Excellent Range (59.5-63.5%)",
                "status": "Very Good",
                "comment": "Within acceptable trade boundaries for premium round cuts."
            })
            overall_score -= 5
        elif depth > 64.0:
            evaluations.append({
                "metric": "Total Depth",
                "value": f"{depth:.1f}%",
                "grade": "Too Deep (> 64%)",
                "status": "Nail-head Risk",
                "comment": "Diamond hides carat weight in base/pavilion; face-up size appears smaller than actual weight."
            })
            overall_score -= 25
        else:
            evaluations.append({
                "metric": "Total Depth",
                "value": f"{depth:.1f}%",
                "grade": "Shallow Cut (< 59%)",
                "status": "Fish-eye Risk",
                "comment": "Light passes straight through pavilion without reflecting back to viewer's eyes."
            })
            overall_score -= 20

        # 3. L/W Ratio (Symmetry)
        if ratio:
            if ratio <= 1.02:
                evaluations.append({
                    "metric": "Length-to-Width Ratio",
                    "value": f"{ratio:.2f}",
                    "grade": "Near-Perfect Circularity (1.00-1.02)",
                    "status": "Optimal",
                    "comment": "Exceptional round symmetry."
                })
            else:
                evaluations.append({
                    "metric": "Length-to-Width Ratio",
                    "value": f"{ratio:.2f}",
                    "grade": f"Oval Out-of-Round (> 1.03)",
                    "status": "Sub-optimal",
                    "comment": "Visible out-of-round deviation."
                })
                overall_score -= 10

        overall_score = max(30, min(100, overall_score))

        return {
            "shape": shape,
            "overall_proportion_score": overall_score,
            "grade_label": "Super-Ideal Cut" if overall_score >= 95 else ("Ideal Proportion" if overall_score >= 85 else "Commercial Standard"),
            "evaluations": evaluations,
            "ratio": ratio
        }

    @classmethod
    def ask_assistant(cls, query: str, context_diamond: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Processes jeweller questions with deep domain expertise.
        """
        q_lower = query.lower().strip()
        response_title = "Gemological Intelligence Advisory"

        # 1. Carat Price Jumps / Magic Sizes
        if any(w in q_lower for w in ["magic size", "carat jump", "exponential", "threshold", "price cliff"]):
            response_text = (
                "**Magic Carat Sizes & Exponential Pricing:**\n\n"
                "In diamond trading, prices jump exponentially at key psychological thresholds: **0.50 ct, 0.70 ct, 0.90 ct, 1.00 ct, 1.50 ct, 2.00 ct, 3.00 ct, and 5.00 ct**.\n\n"
                "• **The 0.99 ct vs 1.00 ct Rule:** A 0.99 ct diamond can trade at a 15% to 25% discount compared to an identical 1.00 ct stone, despite being virtually indistinguishable to the naked eye.\n"
                "• **Trade Strategy:** Savvy buyers look for 'under-size' diamonds (e.g., 0.90-0.97 ct or 1.40-1.48 ct) to maximize face-up spread while avoiding the steep premium."
            )
            tags = ["Carat Pricing", "Wholesale Tactics", "Magic Sizes"]

        # 2. Lab-Grown vs Natural Pricing Dynamics
        elif any(w in q_lower for w in ["lab-grown", "lab grown", "cvd", "hpht", "synthetic", "natural vs lab"]):
            response_text = (
                "**Natural vs. Lab-Grown Diamond Valuation Dynamics:**\n\n"
                "• **Natural Diamonds:** Valuation is driven by geological rarity, deep historical auction data, and limited supply. High grades (D-F, VVS+) maintain long-term asset value retention.\n"
                "• **Lab-Grown Diamonds (CVD / HPHT):** Chemically and optically identical carbon crystals, but production costs continue to drop with scalable reactor capacity.\n"
                "• **Market Spread:** Lab-grown diamonds currently trade at a **75% to 88% discount** to equivalent natural mined diamonds in wholesale markets."
            )
            tags = ["Lab-Grown", "CVD/HPHT", "Market Spread"]

        # 3. Fluorescence Impact
        elif any(w in q_lower for w in ["fluorescence", "blue", "medium blue", "strong blue", "milky"]):
            response_text = (
                "**Fluorescence Trade Impact by Color Tier:**\n\n"
                "• **On D–F (Colorless) Diamonds:** Medium to Strong Blue fluorescence typically incurs a **5% to 15% wholesale discount** because the trade fears potential 'milky' or 'oily' haziness in direct sunlight (though only ~3% actually exhibit haze).\n"
                "• **On I–M (Warm Tint) Diamonds:** Medium to Strong Blue fluorescence often commands a **neutral or slight premium** because the blue complimentary color visually cancels yellow tints, making the stone face up 1 to 2 shades whiter."
            )
            tags = ["Fluorescence", "Colorless", "Trade Pricing"]

        # 4. Tolkowsky & Ideal Cut Proportions
        elif any(w in q_lower for w in ["tolkowsky", "ideal cut", "table", "depth", "proportions", "light leakage"]):
            response_text = (
                "**Tolkowsky Ideal Proportions (Marcel Tolkowsky, 1919):**\n\n"
                "• **Table %:** 53.0% to 57.0% (Optimal for maximum fire & scintillation)\n"
                "• **Total Depth %:** 61.0% to 62.5% (Prevents fish-eye & nail-head defects)\n"
                "• **Crown Angle:** 34.0° to 35.0°\n"
                "• **Pavilion Angle:** 40.6° to 41.0°\n"
                "• **Girdle:** Thin to Medium, Faceted (3.0% - 3.5%)\n"
                "• **Culet:** None / Pointed (prevents dark center window)"
            )
            tags = ["Tolkowsky", "GIA Excellent", "Optical Physics"]

        # 5. Clarity Grades & Eye-Cleanliness
        elif any(w in q_lower for w in ["clarity", "vvs", "vs1", "vs2", "si1", "eye clean", "inclusions"]):
            response_text = (
                "**Clarity & Eye-Clean Trade Standards:**\n\n"
                "• **FL / IF (Flawless / Internally Flawless):** Collector & investment tier; < 0.5% of gem quality diamonds.\n"
                "• **VVS1 / VVS2 (Very Very Slightly Included):** Minute pinpoints only visible under 10x-20x binocular microscope.\n"
                "• **VS1 / VS2 (Very Slightly Included):** The sweet spot for luxury retail. 100% eye-clean with excellent resale liquidity.\n"
                "• **SI1 (Slightly Included):** 85% eye-clean if inclusions are white feathers or translucent crystals away from table center."
            )
            tags = ["Clarity", "Eye-Clean", "Investment Grade"]

        # Default General Advisory
        else:
            response_text = (
                f"**GemForecast Intelligence Overview for '{query}':**\n\n"
                "In professional diamond appraisal, accurate valuation requires balancing the **4Cs (Carat, Color, Clarity, Cut)** alongside proportion geometry (Table % / Depth %), certificate provenance (GIA Report Check), and empirical wholesale database comparables.\n\n"
                "• **Key Advice:** Always verify the report number against the official GIA database and check comparable cluster density in our 193.5k verified historical benchmark."
            )
            tags = ["Appraisal Protocol", "GIA Verification", "Valuation Engine"]

        return {
            "title": response_title,
            "answer": response_text,
            "tags": tags,
            "context_attached": bool(context_diamond)
        }
