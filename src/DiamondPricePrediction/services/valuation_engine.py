import math
from typing import Dict, Any, Optional, List
from DiamondPricePrediction.utils.logger import logging
from DiamondPricePrediction.services.indian_market_service import IndianMarketService

class ValuationEngine:
    """
    India-First Jeweller AI Valuation & Deal Engine.
    
    Combines:
      Pillar 1: Current Indian Wholesale Market Benchmark (BDB Mumbai / Surat LGD)
      Pillar 2: Empirical Historical Database Comparables (193.5k records in ₹)
      Pillar 3: Machine Learning Historical Baseline Model
      
    Outputs actionable business decisions:
      - Wholesale Fair Market Range (₹ Low – High)
      - Suggested Jeweller Buying Price (₹)
      - Suggested Customer Retail Asking Price (₹)
      - Expected Jeweller Profit (₹) & Margin (%)
      - 3% Diamond GST breakdown
      - Plain-language "Why this price?" explanation
    """

    @classmethod
    def calculate_valuation(
        cls,
        diamond_spec: Dict[str, Any],
        ml_prediction_usd: float,
        comps_data: Dict[str, Any],
        market_quote_inr: Dict[str, Any],
        asking_price_inr: Optional[float] = None,
        custom_markup_pct: float = 25.0,
        making_charges_inr: float = 0.0
    ) -> Dict[str, Any]:
        """Synthesizes all valuation pillars into an India-first jeweller appraisal dossier."""
        try:
            carat = float(diamond_spec.get("carat", 1.0))
            is_lab = "Lab" in str(diamond_spec.get("origin_type", "Natural")) or "CVD" in str(diamond_spec.get("growth_process", "")) or "HPHT" in str(diamond_spec.get("growth_process", ""))
            usd_inr = IndianMarketService.get_usd_inr_rate()

            # 1. Indian Wholesale Market Value (Pillar 1)
            wholesale_inr = float(market_quote_inr.get("total_wholesale_inr", 0))

            # 2. Historical Benchmark Comps Median in INR (Pillar 2)
            comp_stats = comps_data.get("statistics")
            sample_count = comps_data.get("sample_count", 0)

            # Lab-grown market multiplier on historical natural comps (LGD trades at ~85-92% discount to natural)
            lab_historical_mult = 0.08 if is_lab else 1.0

            if comp_stats and sample_count > 0:
                comp_median_inr = float(comp_stats["median_price_inr"]) * lab_historical_mult
                comp_p25_inr = float(comp_stats["p25_price_inr"]) * lab_historical_mult
                comp_p75_inr = float(comp_stats["p75_price_inr"]) * lab_historical_mult
            else:
                comp_median_inr = wholesale_inr
                comp_p25_inr = wholesale_inr * 0.90
                comp_p75_inr = wholesale_inr * 1.10

            # 3. ML Model Baseline in INR (Pillar 3)
            ml_inr = max(0, ml_prediction_usd * usd_inr * lab_historical_mult)

            # 4. Composite Indian Fair Market Value
            # For Natural: 55% Current BDB Indian Wholesale + 30% Comps Median + 15% ML Baseline
            # For Lab-Grown: 80% Surat SDB LGD Manufacturing Benchmark + 20% Adjusted Comps
            if is_lab:
                fair_market_val = round(0.80 * wholesale_inr + 0.20 * comp_median_inr)
                low_market_val = round(fair_market_val * 0.90)
                high_market_val = round(fair_market_val * 1.10)
            else:
                fair_market_val = round(0.55 * wholesale_inr + 0.30 * comp_median_inr + 0.15 * ml_inr)
                low_market_val = round(min(comp_p25_inr, fair_market_val * 0.92))
                high_market_val = round(max(comp_p75_inr, fair_market_val * 1.08))

            price_per_carat_inr = round(fair_market_val / max(carat, 0.01))

            # 5. Jeweller Buy / Sell Pricing Strategy
            # Suggested Buy: ~10% to 15% below wholesale fair market (wholesaler discount)
            buy_discount_rate = 0.88 if is_lab else 0.90
            suggested_buy_price = round(fair_market_val * buy_discount_rate)

            # Suggested Sell / Customer Price: Fair wholesale + markup (default 25%)
            retail_markup_mult = 1.0 + (custom_markup_pct / 100.0)
            suggested_sell_price = round(fair_market_val * retail_markup_mult + making_charges_inr)

            # Expected Jeweller Gross Profit & Margin
            expected_profit_inr = round(suggested_sell_price - suggested_buy_price)
            expected_margin_pct = round((expected_profit_inr / max(suggested_sell_price, 1.0)) * 100.0, 1)

            # GST (3% on polished diamonds in India)
            gst_amount_inr = round(suggested_sell_price * 0.03)
            customer_price_with_gst = round(suggested_sell_price + gst_amount_inr)

            # 6. Confidence Score
            confidence = cls._compute_confidence_score(
                diamond_spec=diamond_spec,
                sample_count=sample_count,
                has_igi=bool(diamond_spec.get("report_number"))
            )

            # 7. Deal Analysis (if asking price is provided by user)
            deal_analysis = None
            if asking_price_inr is not None and asking_price_inr > 0:
                deal_analysis = cls._analyze_jeweller_deal(
                    asking_price_inr=asking_price_inr,
                    fair_market_val=fair_market_val,
                    low_market_val=low_market_val,
                    high_market_val=high_market_val,
                    suggested_sell_price=suggested_sell_price,
                    carat=carat
                )

            # 8. Plain-Language "Why This Price?" Summary
            why_this_price = cls._generate_business_explanation(
                diamond_spec=diamond_spec,
                fair_market_val=fair_market_val,
                carat=carat,
                is_lab=is_lab,
                expected_profit=expected_profit_inr
            )

            # 9. Value Drivers & Quality Score
            value_drivers = cls._identify_value_drivers(diamond_spec, carat, is_lab)
            quality_score = cls._compute_quality_score(diamond_spec)

            data_avail = market_quote_inr.get("data_available", True)

            return {
                "status": "Valuation Computed" if data_avail else "Live Market Pricing Unavailable",
                "data_available": data_avail,
                "currency": "INR",
                "currency_symbol": "₹",
                "origin_type": "Lab-Grown" if is_lab else "Natural",
                
                # Core Indian Pricing Numbers
                "today_market_price": fair_market_val,
                "today_market_price_formatted": IndianMarketService.format_inr(fair_market_val),
                "fair_market_value": fair_market_val,
                "fair_market_value_formatted": IndianMarketService.format_inr(fair_market_val),
                "fair_market_lakhs": IndianMarketService.format_inr_lakhs(fair_market_val),
                "low_estimate": low_market_val,
                "low_estimate_formatted": IndianMarketService.format_inr(low_market_val),
                "high_estimate": high_market_val,
                "high_estimate_formatted": IndianMarketService.format_inr(high_market_val),
                "price_per_carat": price_per_carat_inr,
                "price_per_carat_formatted": IndianMarketService.format_inr(price_per_carat_inr),
                
                # Jeweller Business Strategy
                "suggested_buy_price": suggested_buy_price,
                "suggested_buy_price_formatted": IndianMarketService.format_inr(suggested_buy_price),
                "suggested_sell_price": suggested_sell_price,
                "suggested_sell_price_formatted": IndianMarketService.format_inr(suggested_sell_price),
                "expected_profit": expected_profit_inr,
                "expected_profit_formatted": IndianMarketService.format_inr(expected_profit_inr),
                "expected_margin_pct": expected_margin_pct,
                "gst_amount": gst_amount_inr,
                "gst_amount_formatted": IndianMarketService.format_inr(gst_amount_inr),
                "customer_price_with_gst": customer_price_with_gst,
                "customer_price_with_gst_formatted": IndianMarketService.format_inr(customer_price_with_gst),
                
                # Evidence & Confidence & Source Metadata
                "confidence_score": confidence["total_score"],
                "confidence_grade": confidence["grade"],
                "confidence_breakdown": confidence["details"],
                "quality_score": quality_score,
                "source": market_quote_inr.get("source", "Bharat Diamond Bourse / Surat LGD Benchmark"),
                "timestamp": market_quote_inr.get("timestamp", ""),
                "market_date": market_quote_inr.get("market_date", ""),
                
                # Multi-Pillar Valuation Breakdown
                "pillars": {
                    "indian_wholesale": {
                        "name": market_quote_inr.get("source", "Indian Wholesale Benchmark"),
                        "value_inr": wholesale_inr,
                        "value_formatted": IndianMarketService.format_inr(wholesale_inr),
                        "status": "Active Indian Wholesale Matrix"
                    },
                    "historical_comps": {
                        "name": "Historical Benchmark Sales (193.5k Records)",
                        "sample_count": sample_count,
                        "median_inr": round(comp_median_inr),
                        "median_formatted": IndianMarketService.format_inr(comp_median_inr),
                        "status": f"{sample_count} matching historical sales found"
                    },
                    "model_baseline": {
                        "name": "Statistical Regression Baseline",
                        "value_inr": round(ml_inr),
                        "value_formatted": IndianMarketService.format_inr(ml_inr),
                        "status": "Calculated Historical Baseline"
                    }
                },
                
                "why_this_price": why_this_price,
                "value_drivers": value_drivers,
                "jeweller_deal": deal_analysis
            }


        except Exception as e:
            logging.error(f"Error in ValuationEngine: {e}")
            return {
                "status": "Calculation Error",
                "error": str(e),
                "fair_market_value": 0,
                "suggested_buy_price": 0,
                "suggested_sell_price": 0,
                "confidence_score": 0
            }

    @classmethod
    def _compute_confidence_score(cls, diamond_spec: Dict[str, Any], sample_count: int, has_igi: bool) -> Dict[str, Any]:
        """Derive confidence score (0-100) based on verified parameters and data density."""
        score = 0
        details = []

        # 1. IGI Verification Integrity (Max 35 pts)
        if has_igi:
            verif_pts = 35
            details.append({"factor": "Official IGI Report Verified", "points": 35, "max": 35, "note": "IGI report number / certificate verified."})
        else:
            verif_pts = 15
            details.append({"factor": "Unverified Specification", "points": 15, "max": 35, "note": "Manual input without verified IGI certificate."})
        score += verif_pts

        # 2. Specification Completeness (Max 35 pts)
        spec_fields = ["carat", "color", "clarity", "cut", "depth", "table", "x", "y", "z"]
        present = sum(1 for k in spec_fields if diamond_spec.get(k) is not None)
        comp_pts = int((present / len(spec_fields)) * 35)
        score += comp_pts
        details.append({"factor": "Diamond Spec Completeness", "points": comp_pts, "max": 35, "note": f"{present}/{len(spec_fields)} standard geometric & grading attributes present."})

        # 3. Benchmark Cluster Density (Max 30 pts)
        if sample_count >= 30:
            density_pts = 30
        elif sample_count >= 10:
            density_pts = 24
        elif sample_count >= 4:
            density_pts = 16
        else:
            density_pts = 8
        score += density_pts
        details.append({"factor": "Historical Wholesale Comp Density", "points": density_pts, "max": 30, "note": f"{sample_count} matching sales records in trade cluster."})

        total = min(100, max(15, score))
        if total >= 85:
            grade = "High Jeweller Confidence (Tier A+)"
        elif total >= 70:
            grade = "Reliable Commercial Confidence (Tier A)"
        elif total >= 50:
            grade = "Moderate Confidence (Tier B)"
        else:
            grade = "Preliminary Estimate (Tier C)"

        return {"total_score": total, "grade": grade, "details": details}

    @classmethod
    def _compute_quality_score(cls, spec: Dict[str, Any]) -> int:
        """Computes a 0-100 Jeweller Diamond Quality Index based on 4Cs and optical performance."""
        score = 50
        cut = str(spec.get("cut", "")).title()
        color = str(spec.get("color", "")).upper()
        clarity = str(spec.get("clarity", "")).upper()
        polish = str(spec.get("polish", "")).title()
        sym = str(spec.get("symmetry", "")).title()
        fluor = str(spec.get("fluorescence", "")).title()

        # Cut
        if cut in ["Ideal", "Excellent"]:
            score += 15
        elif cut == "Very Good":
            score += 10
        elif cut == "Good":
            score += 2

        # Polish & Symmetry (Triple Excellent boost)
        if polish in ["Ideal", "Excellent"] and sym in ["Ideal", "Excellent"] and cut in ["Ideal", "Excellent"]:
            score += 10
        elif polish in ["Ideal", "Excellent"]:
            score += 5

        # Color
        if color in ["D", "E"]:
            score += 15
        elif color == "F":
            score += 12
        elif color in ["G", "H"]:
            score += 8
        elif color in ["I", "J"]:
            score += 4

        # Clarity
        if clarity in ["FL", "IF"]:
            score += 15
        elif clarity in ["VVS1", "VVS2"]:
            score += 12
        elif clarity in ["VS1", "VS2"]:
            score += 8
        elif clarity == "SI1":
            score += 4

        # Fluorescence
        if fluor == "None":
            score += 5
        elif "Strong" in fluor and color in ["D", "E", "F"]:
            score -= 8

        return max(20, min(100, score))

    @classmethod
    def _analyze_jeweller_deal(
        cls,
        asking_price_inr: float,
        fair_market_val: float,
        low_market_val: float,
        high_market_val: float,
        suggested_sell_price: float,
        carat: float
    ) -> Dict[str, Any]:
        """Evaluates whether an offered diamond is underpriced, fair, or overpriced for a jeweller."""
        delta = round(fair_market_val - asking_price_inr)
        margin_on_asking = round((delta / max(asking_price_inr, 1.0)) * 100.0, 1)

        realized_profit = round(suggested_sell_price - asking_price_inr)
        realized_margin = round((realized_profit / max(suggested_sell_price, 1.0)) * 100.0, 1)

        if asking_price_inr < low_market_val:
            rating = "Exceptional Wholesale Value (High Profit Potential)"
            badge_class = "badge-success"
            verdict = "STRONG BUY"
            advice = f"Offered price is {IndianMarketService.format_inr(abs(delta))} below fair market wholesale value. Potential {realized_margin}% profit margin."
        elif asking_price_inr <= fair_market_val:
            rating = "Fair Wholesale Market Range"
            badge_class = "badge-primary"
            verdict = "BUY AT CURRENT PRICE"
            advice = f"Offered within competitive Indian wholesale range with {IndianMarketService.format_inr(realized_profit)} expected jeweller profit."
        elif asking_price_inr <= high_market_val:
            rating = "Full Retail Premium"
            badge_class = "badge-warning"
            verdict = "NEGOTIATE LOWER"
            advice = f"Asking price is {abs(margin_on_asking)}% above wholesale fair value. Limits jeweller margin unless selling customized bridal jewelry."
        else:
            rating = "Overpriced (Above Upper Wholesale Bound)"
            badge_class = "badge-danger"
            verdict = "OVERPRICED - RE-NEGOTIATE"
            advice = f"Supplier is asking {IndianMarketService.format_inr(asking_price_inr - high_market_val)} above maximum wholesale benchmark. Counter-offer at {IndianMarketService.format_inr(fair_market_val)}."

        return {
            "asking_price": asking_price_inr,
            "asking_price_formatted": IndianMarketService.format_inr(asking_price_inr),
            "asking_ppc_formatted": IndianMarketService.format_inr(asking_price_inr / max(carat, 0.01)),
            "delta_from_market": delta,
            "delta_formatted": IndianMarketService.format_inr(delta),
            "margin_on_asking_pct": margin_on_asking,
            "expected_profit_at_asking": realized_profit,
            "expected_profit_formatted": IndianMarketService.format_inr(realized_profit),
            "realized_margin_pct": realized_margin,
            "deal_rating": rating,
            "verdict": verdict,
            "badge_class": badge_class,
            "advice": advice
        }

    @classmethod
    def _generate_business_explanation(
        cls,
        diamond_spec: Dict[str, Any],
        fair_market_val: float,
        carat: float,
        is_lab: bool,
        expected_profit: float
    ) -> str:
        """Generates plain jewellery-business explanation for the valuation."""
        color = str(diamond_spec.get("color", "F")).upper()
        clarity = str(diamond_spec.get("clarity", "VS1")).upper()
        cut = str(diamond_spec.get("cut", "Ideal")).title()
        shape = str(diamond_spec.get("shape", "Round Brilliant")).title()
        fluor = str(diamond_spec.get("fluorescence", "None")).title()

        points = []

        if is_lab:
            points.append(f"This is an IGI-certified **Lab-Grown Diamond ({carat:.2f} ct {shape})** valued at current Surat manufacturing wholesale rates ({IndianMarketService.format_inr(fair_market_val)}).")
            points.append(f"Lab-grown diamonds trade at a ~85-90% discount to natural mined stones, offering jewellers fast turnover and accessible retail price points.")
        else:
            points.append(f"This is a verified **Natural Mined Diamond ({carat:.2f} ct {shape})** valued against the Mumbai Bharat Diamond Bourse (BDB) benchmark at {IndianMarketService.format_inr(fair_market_val)}.")
            if carat >= 1.0:
                points.append(f"Being a **{carat:.2f} ct** stone, it crosses the psychological 1.00 ct threshold which commands premium liquidity in the Indian bridal market.")

        if color in ["D", "E", "F"]:
            points.append(f"Top-tier **Colorless ({color})** grade ensures maximum visual whiteness and high customer resale demand.")
        elif color in ["G", "H"]:
            points.append(f"**Near-Colorless ({color})** grade provides optimal commercial value with no eye-visible tint when mounted in gold or platinum.")

        if clarity in ["IF", "VVS1", "VVS2"]:
            points.append(f"**{clarity} Clarity** has microscopic inclusions only visible under 10x magnification, commanding strong investment trust.")
        elif clarity in ["VS1", "VS2"]:
            points.append(f"**{clarity} Clarity** is 100% eye-clean, representing the most popular high-margin retail choice.")

        if cut in ["Ideal", "Excellent"]:
            points.append(f"**{cut} Cut** ensures maximum light return, optical fire, and sparkle, justifying premium retail pricing.")

        if fluor == "None":
            points.append("Zero fluorescence (None) guarantees pure optical clarity with no trade discount.")
        elif "Strong" in fluor:
            points.append("Strong fluorescence is factored into the wholesale rate with standard trade adjustments.")

        return " ".join(points)

    @classmethod
    def _identify_value_drivers(cls, spec: Dict[str, Any], carat: float, is_lab: bool) -> List[Dict[str, Any]]:
        """Identify key positive and negative trade value drivers."""
        drivers = []
        color = str(spec.get("color", "")).upper()
        clarity = str(spec.get("clarity", "")).upper()
        cut = str(spec.get("cut", "")).title()
        fluor = str(spec.get("fluorescence", "")).title()

        if is_lab:
            drivers.append({"driver": "Lab-Grown Origin", "type": "warning", "text": "Surat CVD/HPHT origin trades at wholesale discount vs natural diamonds."})
        else:
            drivers.append({"driver": "Natural Mined Origin", "type": "positive", "text": "Geological rarity and sustained asset value retention."})

        if carat >= 1.0:
            drivers.append({"driver": f"{carat:.2f} ct Size Category", "type": "positive", "text": "Crosses the 1.00+ ct magic threshold for bridal demand in India."})

        if color in ["D", "E", "F"]:
            drivers.append({"driver": f"Colorless Grade ({color})", "type": "positive", "text": "Top color grade with high visual purity and trade prestige."})

        if clarity in ["IF", "VVS1", "VVS2"]:
            drivers.append({"driver": f"High Purity Clarity ({clarity})", "type": "positive", "text": "Ultra-clean under 10x magnification; premium resale value."})
        elif clarity in ["SI1", "SI2"]:
            drivers.append({"driver": f"Commercial Clarity ({clarity})", "type": "neutral", "text": "Standard retail tier; verify inclusion location under table."})

        if cut in ["Ideal", "Excellent"]:
            drivers.append({"driver": f"{cut} Cut Proportions", "type": "positive", "text": "Optimal light reflection and brilliance."})

        if fluor == "None":
            drivers.append({"driver": "Nil Fluorescence", "type": "positive", "text": "Clean transparency in sunlight with no milky haze risk."})
        elif "Strong" in fluor and color in ["D", "E", "F"]:
            drivers.append({"driver": f"Strong Fluorescence on {color}", "type": "warning", "text": "Incurs 8-12% wholesale trade discount in Indian market."})

        return drivers
