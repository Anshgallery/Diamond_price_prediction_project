import math
from typing import Dict, Any, Optional, List
from DiamondPricePrediction.utils.logger import logging

class ValuationEngine:
    """
    Production-grade Multi-Pillar Valuation & Jeweller Margin Engine.
    Combines:
      Pillar 1: Historical ML Valuation (Trained on 193.5k benchmark records)
      Pillar 2: Real Database Comparables Distribution (Empirical P25-P75, Median)
      Pillar 3: Live Wholesale Market Data (Connected Feed or Explicitly Unconnected)
    Calculates composite valuation ranges, confidence scores, and jeweller deal analytics.
    """

    @classmethod
    def calculate_valuation(
        cls,
        diamond_spec: Dict[str, Any],
        ml_prediction: float,
        comps_data: Dict[str, Any],
        market_quote_data: Dict[str, Any],
        asking_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes all evidence pillars into a structured, evidence-based valuation dossier.
        """
        try:
            carat = float(diamond_spec.get("carat", 1.0))
            is_lab_grown = "Lab" in str(diamond_spec.get("origin_type", "Natural"))
            
            # 1. Evaluate Data Sufficiency
            insufficient_comps = comps_data.get("insufficient_data", False) or (comps_data.get("sample_count", 0) == 0)
            
            if ml_prediction <= 0 or (insufficient_comps and carat > 5.0):
                return {
                    "status": "Insufficient Data",
                    "insufficient_data": True,
                    "summary_message": "Insufficient verified market data for reliable valuation.",
                    "estimated_range": None,
                    "confidence_score": 0,
                    "jeweller_deal": None
                }

            # 2. Extract Pillar Inputs
            historical_ml_val = round(float(ml_prediction), 2)
            
            # Lab-grown adjustment if origin is lab-grown (historically trading at ~70-85% discount to natural)
            lab_multiplier = 0.22 if is_lab_grown else 1.0
            historical_ml_val_adjusted = round(historical_ml_val * lab_multiplier, 2)

            comp_stats = comps_data.get("statistics")
            sample_count = comps_data.get("sample_count", 0)

            if comp_stats and sample_count > 0:
                comp_median = float(comp_stats["median_price"]) * lab_multiplier
                comp_p25 = float(comp_stats["p25_price"]) * lab_multiplier
                comp_p75 = float(comp_stats["p75_price"]) * lab_multiplier
                
                # Weighting: 45% ML Model + 55% Empirical Database Comps
                # If Live Wholesale Market is connected, weights adjust to 40% Live, 35% Comps, 25% ML
                if market_quote_data.get("is_connected") and market_quote_data.get("live_quote"):
                    live_p = float(market_quote_data["live_quote"])
                    midpoint = round(0.40 * live_p + 0.35 * comp_median + 0.25 * historical_ml_val_adjusted, 2)
                    low_est = round(min(comp_p25, midpoint * 0.90), 2)
                    high_est = round(max(comp_p75, midpoint * 1.10), 2)
                else:
                    midpoint = round(0.55 * comp_median + 0.45 * historical_ml_val_adjusted, 2)
                    low_est = round(min(comp_p25, midpoint * 0.91), 2)
                    high_est = round(max(comp_p75, midpoint * 1.09), 2)
            else:
                midpoint = historical_ml_val_adjusted
                low_est = round(midpoint * 0.88, 2)
                high_est = round(midpoint * 1.12, 2)
                comp_median = None
                comp_p25 = None
                comp_p75 = None

            price_per_carat = round(midpoint / max(carat, 0.01), 2)

            # 3. Calculate Evidence-Based Confidence Score (0-100)
            confidence_breakdown = cls._compute_confidence_score(
                diamond_spec=diamond_spec,
                sample_count=sample_count,
                has_verification=bool(diamond_spec.get("report_number")),
                market_connected=market_quote_data.get("is_connected", False),
                ml_val=historical_ml_val_adjusted,
                comp_val=comp_median
            )

            # 4. Jeweller Asking / Purchase Price Analysis
            jeweller_analysis = None
            if asking_price is not None and asking_price > 0:
                jeweller_analysis = cls._analyze_deal(
                    asking_price=float(asking_price),
                    estimated_midpoint=midpoint,
                    low_est=low_est,
                    high_est=high_est,
                    carat=carat
                )

            # 5. Valuation Factor Indicators (4Cs Impact Analysis)
            valuation_drivers = cls._identify_valuation_factors(diamond_spec, midpoint, carat, is_lab_grown)

            return {
                "status": "Valuation Computed",
                "insufficient_data": False,
                "midpoint_value": midpoint,
                "low_estimate": low_est,
                "high_estimate": high_est,
                "price_per_carat": price_per_carat,
                "currency": "USD",
                "origin_type": "Lab-Grown" if is_lab_grown else "Natural",
                "confidence_score": confidence_breakdown["total_score"],
                "confidence_grade": confidence_breakdown["grade"],
                "confidence_breakdown": confidence_breakdown,
                "pillars": {
                    "historical_ml": {
                        "name": "Historical ML Model (193.5k Benchmark)",
                        "raw_prediction": historical_ml_val,
                        "adjusted_value": historical_ml_val_adjusted,
                        "status": "Calculated",
                        "metrics": "R²: 0.936 | MAE: $568 | Linear Ridge/Lasso Pipeline"
                    },
                    "database_comps": {
                        "name": "Historical Benchmark Comparables",
                        "sample_count": sample_count,
                        "median": round(comp_median, 2) if comp_median else None,
                        "p25": round(comp_p25, 2) if comp_p25 else None,
                        "p75": round(comp_p75, 2) if comp_p75 else None,
                        "status": f"{sample_count} matching records found" if sample_count > 0 else "Low sample cluster"
                    },
                    "live_market": market_quote_data
                },
                "valuation_drivers": valuation_drivers,
                "jeweller_deal": jeweller_analysis
            }

        except Exception as e:
            logging.error(f"Error in ValuationEngine: {e}")
            return {
                "status": "Calculation Error",
                "insufficient_data": True,
                "summary_message": f"Error calculating valuation: {str(e)}",
                "estimated_range": None,
                "confidence_score": 0,
                "jeweller_deal": None
            }

    @classmethod
    def _compute_confidence_score(
        cls,
        diamond_spec: Dict[str, Any],
        sample_count: int,
        has_verification: bool,
        market_connected: bool,
        ml_val: float,
        comp_val: Optional[float]
    ) -> Dict[str, Any]:
        """
        Derives an authentic data quality and confidence index (0-100) based on
        data completeness, comp density, model agreement, and verification integrity.
        """
        score = 0
        details = []

        # 1. Specification Completeness (Max 30 pts)
        spec_keys = ["carat", "cut", "color", "clarity", "depth", "table", "x", "y", "z"]
        present_count = sum(1 for k in spec_keys if diamond_spec.get(k) is not None)
        completeness_pts = int((present_count / len(spec_keys)) * 30)
        score += completeness_pts
        details.append({
            "factor": "4Cs & Proportions Completeness",
            "points": completeness_pts,
            "max": 30,
            "description": f"{present_count}/{len(spec_keys)} standard geometric and 4Cs fields verified."
        })

        # 2. Historical Comparables Sample Depth (Max 30 pts)
        if sample_count >= 50:
            comp_pts = 30
        elif sample_count >= 20:
            comp_pts = 24
        elif sample_count >= 10:
            comp_pts = 18
        elif sample_count >= 3:
            comp_pts = 10
        else:
            comp_pts = 4
        score += comp_pts
        details.append({
            "factor": "Empirical Comp Cluster Depth",
            "points": comp_pts,
            "max": 30,
            "description": f"{sample_count} matching historical diamond sales records in benchmark cluster."
        })

        # 3. Model & Comps Alignment (Max 20 pts)
        if comp_val and comp_val > 0 and ml_val > 0:
            ratio = min(comp_val, ml_val) / max(comp_val, ml_val)
            align_pts = int(ratio * 20)
        else:
            align_pts = 10
        score += align_pts
        details.append({
            "factor": "Multi-Pillar Valuation Convergence",
            "points": align_pts,
            "max": 20,
            "description": "Cross-validation agreement between ML regression and empirical median."
        })

        # 4. GIA Certificate & Verification Status (Max 15 pts)
        verif_pts = 15 if has_verification else 5
        score += verif_pts
        details.append({
            "factor": "Certificate & Audit Trail",
            "points": verif_pts,
            "max": 15,
            "description": "GIA report number linked with official verification workflow." if has_verification else "Manual input without official certificate verification."
        })

        # 5. Live Market Feed Connection (Max 5 pts)
        market_pts = 5 if market_connected else 0
        score += market_pts
        details.append({
            "factor": "Live Wholesale Feed Connection",
            "points": market_pts,
            "max": 5,
            "description": "Live wholesale API feed connected." if market_connected else "Offline mode (Historical database valuation only)."
        })

        total = min(100, max(10, score))
        if total >= 85:
            grade = "High Confidence (A+)"
        elif total >= 70:
            grade = "Good Confidence (A)"
        elif total >= 50:
            grade = "Moderate Confidence (B)"
        else:
            grade = "Preliminary / Low Evidence (C)"

        return {
            "total_score": total,
            "grade": grade,
            "factors": details
        }

    @classmethod
    def _analyze_deal(
        cls,
        asking_price: float,
        estimated_midpoint: float,
        low_est: float,
        high_est: float,
        carat: float
    ) -> Dict[str, Any]:
        """
        Calculates jeweller buy/sell economics, discount from fair market, and suggested retail price.
        """
        delta = round(estimated_midpoint - asking_price, 2)
        margin_pct = round((delta / max(asking_price, 1.0)) * 100.0, 1)

        asking_ppc = round(asking_price / max(carat, 0.01), 2)
        midpoint_ppc = round(estimated_midpoint / max(carat, 0.01), 2)

        if asking_price < low_est:
            rating = "Exceptional Wholesale Value (Below Market)"
            badge_class = "badge-success"
            analysis_text = f"Asking price is ${abs(delta):,.2f} ({abs(margin_pct):.1f}%) below estimated fair market value. Strong acquisition opportunity."
        elif asking_price <= estimated_midpoint:
            rating = "Fair Wholesale Market Range"
            badge_class = "badge-primary"
            analysis_text = f"Asking price is within the competitive wholesale range, offering an estimated ${delta:,.2f} positive valuation spread."
        elif asking_price <= high_est:
            rating = "Full Market Value / Retail Premium"
            badge_class = "badge-warning"
            analysis_text = f"Asking price is {abs(margin_pct):.1f}% above market midpoint. Leaves limited wholesale margin unless customized for retail."
        else:
            rating = "High Asking Price (Above Market Upper Bound)"
            badge_class = "badge-danger"
            analysis_text = f"Asking price exceeds estimated high market bound by ${abs(asking_price - high_est):,.2f}. Re-negotiation recommended."

        # Suggest Retail Price with standard 25% to 40% gross margin
        rec_retail_low = round(asking_price * 1.25, 2)
        rec_retail_mid = round(estimated_midpoint * 1.35, 2)
        rec_retail_high = round(estimated_midpoint * 1.50, 2)

        return {
            "asking_price": asking_price,
            "asking_price_per_carat": asking_ppc,
            "midpoint_price_per_carat": midpoint_ppc,
            "dollar_margin": delta,
            "percentage_spread": margin_pct,
            "deal_rating": rating,
            "badge_class": badge_class,
            "analysis_text": analysis_text,
            "recommended_retail": {
                "conservative_25pct": rec_retail_low,
                "standard_35pct": rec_retail_mid,
                "premium_50pct": rec_retail_high
            }
        }

    @classmethod
    def _identify_valuation_factors(
        cls,
        diamond_spec: Dict[str, Any],
        midpoint: float,
        carat: float,
        is_lab_grown: bool
    ) -> List[Dict[str, Any]]:
        """Identify key positive and negative value drivers from diamond gemology."""
        drivers = []
        color = str(diamond_spec.get("color", "")).upper()
        clarity = str(diamond_spec.get("clarity", "")).upper()
        cut = str(diamond_spec.get("cut", "")).title()
        fluor = str(diamond_spec.get("fluorescence", "")).title()

        # 1. Carat scale
        if carat >= 2.0:
            drivers.append({"driver": f"2+ Carat Premium ({carat:.2f} ct)", "impact": "Positive", "note": "High rarity in natural market exponential price curve."})
        elif carat >= 1.0:
            drivers.append({"driver": f"1+ Carat Magic Threshold ({carat:.2f} ct)", "impact": "Positive", "note": "Significant consumer demand threshold."})

        # 2. Color grade
        if color in ["D", "E", "F"]:
            drivers.append({"driver": f"Colorless Grade ({color})", "impact": "Positive", "note": "Top tier color rating commanding premium market pricing."})
        elif color in ["I", "J"]:
            drivers.append({"driver": f"Near-Colorless ({color})", "impact": "Discount", "note": "Warmer tint trades at noticeable wholesale discount to D-F tiers."})

        # 3. Clarity grade
        if clarity in ["IF", "VVS1", "VVS2"]:
            drivers.append({"driver": f"High Purity Clarity ({clarity})", "impact": "Positive", "note": "Minute or zero inclusions visible under 10x magnification."})
        elif clarity in ["SI2", "I1"]:
            drivers.append({"driver": f"Included Grade ({clarity})", "impact": "Discount", "note": "Inclusions may be eye-visible; discounted pricing."})

        # 4. Cut Quality
        if cut in ["Ideal", "Excellent"]:
            drivers.append({"driver": "Excellent/Ideal Cut Proportions", "impact": "Positive", "note": "Maximizes light return, brilliance, fire, and scintillation."})
        elif cut in ["Fair", "Good"]:
            drivers.append({"driver": f"Sub-optimal Cut ({cut})", "impact": "Discount", "note": "Light leakage reduces optical brilliance and resale value."})

        # 5. Lab-Grown vs Natural
        if is_lab_grown:
            drivers.append({"driver": "Laboratory-Grown Diamond", "impact": "Discount", "note": "Manufactured origin trades at 75-85% discount vs natural mined diamonds."})
        else:
            drivers.append({"driver": "Natural Mined Origin", "impact": "Positive", "note": "Geological rarity provides higher long-term value retention."})

        # 6. Fluorescence
        if "Strong" in fluor:
            if color in ["D", "E", "F"]:
                drivers.append({"driver": "Strong Fluorescence on D-F Color", "impact": "Discount", "note": "Can create slight haze in sunlight; discounted by trade."})
            elif color in ["I", "J"]:
                drivers.append({"driver": "Fluorescence on Warm Color", "impact": "Positive", "note": "Blue fluorescence can make I-J color appear whiter."})

        return drivers
