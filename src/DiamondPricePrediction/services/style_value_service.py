import math
from typing import Dict, Any, List, Optional
from DiamondPricePrediction.utils.logger import logging

class StyleValueService:
    """
    AI Face & Style-Value Layer for IGI Certified Diamonds.
    
    Categorizes diamonds into:
      1. Premium (Luxury Tier / High-End Optical Brilliance)
      2. Moderate (Balanced Commercial Retail Tier)
      3. Value-Oriented (Maximum Value / Fast Wholesale Turnover Tier)
      
    Generates AI Face Score (0-100), Face Tier, and maps User Pricing Preference Signals
    to target retail markup & profit strategy.
    """

    PREFERENCE_CONFIGS = {
        "premium": {
            "tier": "premium",
            "label": "Premium Luxury Tier",
            "badge_class": "badge-gold",
            "default_markup_pct": 38.0,
            "positioning": "High-end luxury boutique positioning. Maximizes profit per stone for discerning buyers seeking top optical brilliance.",
            "buy_discount_factor": 0.94,
            "sell_multiplier": 1.38
        },
        "moderate": {
            "tier": "moderate",
            "label": "Moderate Commercial Tier",
            "badge_class": "badge-emerald",
            "default_markup_pct": 25.0,
            "positioning": "Standard commercial retail positioning. Balanced margin & steady retail demand.",
            "buy_discount_factor": 0.90,
            "sell_multiplier": 1.25
        },
        "value-oriented": {
            "tier": "value-oriented",
            "label": "Value-Oriented Tier",
            "badge_class": "badge-cyan",
            "default_markup_pct": 14.0,
            "positioning": "Fast turnover / competitive discount positioning. Target for volume wholesale sales and budget-conscious buyers.",
            "buy_discount_factor": 0.85,
            "sell_multiplier": 1.14
        }
    }

    @classmethod
    def evaluate_ai_face_layer(
        cls,
        diamond_spec: Dict[str, Any],
        user_preference_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extracts AI Face / Style-Value tier after IGI extraction and evaluates
        the active Pricing Preference Signal.
        """
        try:
            cut = str(diamond_spec.get("cut", "Ideal")).title()
            color = str(diamond_spec.get("color", "F")).upper()
            clarity = str(diamond_spec.get("clarity", "VS1")).upper()
            polish = str(diamond_spec.get("polish", "Excellent")).title()
            sym = str(diamond_spec.get("symmetry", "Excellent")).title()
            fluor = str(diamond_spec.get("fluorescence", "None")).title()
            table = float(diamond_spec.get("table", 57.0))
            depth = float(diamond_spec.get("depth", 61.8))
            carat = float(diamond_spec.get("carat", 1.0))
            is_lab = "Lab" in str(diamond_spec.get("origin_type", "Natural")) or "CVD" in str(diamond_spec.get("growth_process", "")) or "HPHT" in str(diamond_spec.get("growth_process", ""))

            # Calculate AI Face Score (0 - 100)
            score = 50
            drivers = []

            # 1. Cut Proportions & Optical Symmetry (Max 25 pts)
            if cut in ["Ideal", "Excellent"]:
                score += 15
                drivers.append("Ideal/Excellent cut maximizes light dispersion & scintillation.")
            elif cut == "Very Good":
                score += 8
                drivers.append("Very Good cut provides balanced optical performance.")
            else:
                score += 2
                drivers.append("Standard cut proportioning.")

            if polish in ["Ideal", "Excellent"] and sym in ["Ideal", "Excellent"]:
                score += 10
                drivers.append("Triple Excellent (3EX) polish & symmetry alignment.")

            # 2. Color Purity (Max 20 pts)
            if color in ["D", "E"]:
                score += 20
                drivers.append(f"Top colorless grade ({color}) - supreme optical purity.")
            elif color == "F":
                score += 16
                drivers.append("Colorless (F) grade - highly sought retail white.")
            elif color in ["G", "H"]:
                score += 10
                drivers.append(f"Near colorless ({color}) - optimal commercial value.")
            elif color in ["I", "J"]:
                score += 4
                drivers.append(f"Commercial warm tint ({color}) tier.")

            # 3. Clarity Distinction (Max 20 pts)
            if clarity in ["FL", "IF"]:
                score += 20
                drivers.append(f"Flawless/Internally Flawless ({clarity}) investment tier.")
            elif clarity in ["VVS1", "VVS2"]:
                score += 16
                drivers.append(f"VVS ({clarity}) micro-inclusion purity.")
            elif clarity in ["VS1", "VS2"]:
                score += 10
                drivers.append(f"VS ({clarity}) eye-clean commercial standard.")
            elif clarity in ["SI1", "SI2"]:
                score += 4
                drivers.append(f"SI ({clarity}) value-oriented tier.")

            # 4. Tolkowsky Ideal Table & Depth Bonus (Max 10 pts)
            if 54.0 <= table <= 57.5 and 61.0 <= depth <= 62.5:
                score += 10
                drivers.append("Tolkowsky Ideal Table (54-57.5%) & Depth (61-62.5%) geometry.")
            elif 53.0 <= table <= 59.0 and 59.5 <= depth <= 63.5:
                score += 5
                drivers.append("Excellent geometric table/depth spread.")

            # 5. Fluorescence Impact (Max 5 pts)
            if fluor == "None":
                score += 5
                drivers.append("Nil fluorescence ensures crisp optical transparency.")
            elif "Strong" in fluor and color in ["D", "E", "F"]:
                score -= 8
                drivers.append("Strong fluorescence incurs trade discount on colorless grade.")

            # Clamp face score
            face_score = max(20, min(100, score))

            # Derive AI Face Tier
            if face_score >= 82:
                ai_face_tier = "premium"
            elif face_score >= 62:
                ai_face_tier = "moderate"
            else:
                ai_face_tier = "value-oriented"

            # Determine Active Pricing Preference Signal
            active_signal = (user_preference_override or ai_face_tier).lower()
            if active_signal not in cls.PREFERENCE_CONFIGS:
                active_signal = ai_face_tier

            active_config = cls.PREFERENCE_CONFIGS[active_signal]
            ai_face_config = cls.PREFERENCE_CONFIGS[ai_face_tier]

            return {
                "ai_face_tier": ai_face_tier,
                "ai_face_label": ai_face_config["label"],
                "ai_face_badge_class": ai_face_config["badge_class"],
                "face_score": face_score,
                
                "pricing_preference_signal": active_signal,
                "active_preference_label": active_config["label"],
                "active_badge_class": active_config["badge_class"],
                "target_markup_pct": active_config["default_markup_pct"],
                "positioning_summary": active_config["positioning"],
                "buy_discount_factor": active_config["buy_discount_factor"],
                "sell_multiplier": active_config["sell_multiplier"],
                
                "style_drivers": drivers,
                "available_signals": [
                    {"code": "premium", "label": "Premium Luxury Tier (+38% Markup)", "badge": "badge-gold"},
                    {"code": "moderate", "label": "Moderate Commercial Tier (+25% Markup)", "badge": "badge-emerald"},
                    {"code": "value-oriented", "label": "Value-Oriented Tier (+14% Markup)", "badge": "badge-cyan"}
                ]
            }

        except Exception as e:
            logging.error(f"Error in StyleValueService: {e}")
            fallback = cls.PREFERENCE_CONFIGS["moderate"]
            return {
                "ai_face_tier": "moderate",
                "ai_face_label": fallback["label"],
                "ai_face_badge_class": fallback["badge_class"],
                "face_score": 70,
                "pricing_preference_signal": "moderate",
                "active_preference_label": fallback["label"],
                "active_badge_class": fallback["badge_class"],
                "target_markup_pct": 25.0,
                "positioning_summary": fallback["positioning"],
                "buy_discount_factor": 0.90,
                "sell_multiplier": 1.25,
                "style_drivers": ["Standard commercial diamond geometry."],
                "available_signals": []
            }
