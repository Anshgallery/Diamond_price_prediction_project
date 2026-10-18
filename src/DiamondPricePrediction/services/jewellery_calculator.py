from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from DiamondPricePrediction.services.ibja_gold_service import IBJAGoldService
from DiamondPricePrediction.services.licensed_diamond_service import LicensedDiamondService

class JewelleryCalculator:
    """
    High-Precision Decimal Arithmetic Jewellery Calculation Engine.
    
    Eliminates all IEEE 754 floating-point rounding errors in commercial
    jewellery pricing, metal purity, diamond 4Cs, gemstones, labour, GST,
    and profit margins.
    
    Supports:
      - Gold: 24K (999), 22K (916), 18K (750), 14K (585), 10K (417)
      - Silver: 999 (Fine Silver), 925 (Sterling Silver)
      - Platinum: Pt950, Pt900, Pt850
      - Diamond: 4Cs, IGI/GIA certificate, natural / lab, live rate per carat
      - Ruby: Natural Pigeon Blood / Burmese / Mozambique, carats, live rate per carat
      - Labour & Making: per gram, flat, or percentage
      - GST Breakup: 3% composite jewellery GST (CGST 1.5% + SGST 1.5% or IGST 3.0%)
    """

    GST_RATE_JEWELLERY = Decimal("3.0")   # HSN 7113: 3% composite GST
    CGST_RATE = Decimal("1.5")            # Central GST: 1.5%
    SGST_RATE = Decimal("1.5")            # State GST: 1.5%
    IGST_RATE = Decimal("3.0")            # Integrated GST: 3.0%

    @classmethod
    def calculate(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes end-to-end jewellery appraisal & quotation arithmetic with strict Decimal precision.
        """
        # 1. Metal & Purity
        metal_type = str(params.get("metal_type", "gold")).lower().strip()
        purity = str(params.get("purity") or params.get("purity_str", "18K")).upper().strip()
        raw_net_weight = params.get("net_weight") if params.get("net_weight") is not None else params.get("net_gold_weight", 0.0)
        net_weight = Decimal(str(max(0.0, float(raw_net_weight))))
        wastage_pct = Decimal(str(max(0.0, float(params.get("wastage_pct", 0.0)))))
        custom_base_rate = float(params.get("base_rate") or params.get("custom_gold_rate", 0.0))

        if metal_type in ["gold", "yellow_gold", "white_gold", "rose_gold"]:
            metal_res = IBJAGoldService.calculate_metal_cost(
                net_weight_grams=float(net_weight),
                purity=purity,
                wastage_pct=float(wastage_pct),
                custom_base_rate_24k=custom_base_rate if custom_base_rate > 0 else None
            )
            metal_cost = Decimal(str(metal_res["total_metal_cost"]))
            metal_rate_per_g = Decimal(str(metal_res["rate_per_gram"]))
            gross_weight = Decimal(str(metal_res["gross_weight_grams"]))
            metal_label = f"{purity} Gold ({net_weight}g Net + {wastage_pct}% Wastage)"
            metal_category = "Gold"
        elif metal_type == "silver":
            if custom_base_rate > 0:
                silver_base = Decimal(str(custom_base_rate))
            else:
                curr_rates = IBJAGoldService.get_current_rates()
                silver_base = Decimal(str(curr_rates.get("rates", {}).get("Silver_999", {}).get("rate_per_gram", IBJAGoldService.BASE_BENCHMARK_SILVER_PER_G)))
            if "925" in purity or "sterling" in purity.lower():
                metal_rate_per_g = (silver_base * Decimal("0.925")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                purity_label = "Sterling Silver 925"
            else:
                metal_rate_per_g = silver_base.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                purity_label = "Fine Silver 999"
            waste_w = (net_weight * (wastage_pct / Decimal("100"))).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            gross_weight = (net_weight + waste_w).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            metal_cost = (gross_weight * metal_rate_per_g).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            metal_label = f"{purity_label} ({net_weight}g Net + {wastage_pct}% Wastage)"
            metal_category = "Silver"
        elif metal_type == "platinum":
            if custom_base_rate > 0:
                plat_base = Decimal(str(custom_base_rate))
            else:
                curr_rates = IBJAGoldService.get_current_rates()
                plat_base = Decimal(str(curr_rates.get("rates", {}).get("Platinum_950", {}).get("rate_per_gram", IBJAGoldService.BASE_BENCHMARK_PLATINUM_PER_G)))
            if "900" in purity:
                metal_rate_per_g = (plat_base * Decimal("0.90")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                purity_label = "Platinum Pt900"
            elif "850" in purity:
                metal_rate_per_g = (plat_base * Decimal("0.85")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                purity_label = "Platinum Pt850"
            else:
                metal_rate_per_g = (plat_base * Decimal("0.95")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                purity_label = "Platinum Pt950"
            waste_w = (net_weight * (wastage_pct / Decimal("100"))).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            gross_weight = (net_weight + waste_w).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            metal_cost = (gross_weight * metal_rate_per_g).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            metal_label = f"{purity_label} ({net_weight}g Net + {wastage_pct}% Wastage)"
            metal_category = "Platinum"
        else:
            metal_cost = Decimal("0.00")
            metal_rate_per_g = Decimal("0.00")
            gross_weight = Decimal("0.000")
            metal_label = "No Metal (Loose Stones Only)"
            metal_category = "None"

        # 2. Diamonds
        enable_diamond = bool(params.get("enable_diamond", True))
        if isinstance(params.get("enable_diamond"), str):
            enable_diamond = params.get("enable_diamond").lower() in ("true", "1", "yes", "on")

        if enable_diamond:
            diamond_carat = Decimal(str(max(0.0, float(params.get("diamond_carat", 0.0)))))
            diamond_stones = int(max(1, int(params.get("diamond_stones", 1))))
            diamond_color = str(params.get("diamond_color", "F")).upper().strip()
            diamond_clarity = str(params.get("diamond_clarity", "VS1")).upper().strip()
            diamond_cut = str(params.get("diamond_cut", "Ideal")).title().strip()
            diamond_shape = str(params.get("diamond_shape", "Round Brilliant")).title().strip()
            diamond_origin = str(params.get("diamond_origin", "Natural")).strip()
            diamond_cert = str(params.get("diamond_cert", "IGI Certified")).strip()
            diamond_report_no = str(params.get("diamond_report_no", "")).strip()

            manual_diamond_cost = params.get("diamond_cost")
            if manual_diamond_cost is None and params.get("diamond_rate_per_carat") is not None:
                manual_diamond_cost = float(diamond_carat) * float(params.get("diamond_rate_per_carat"))

            if manual_diamond_cost is not None and float(manual_diamond_cost) > 0:
                diamond_cost = Decimal(str(float(manual_diamond_cost))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                diamond_rate_per_ct = (diamond_cost / diamond_carat).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if diamond_carat > 0 else Decimal("0.00")
                diamond_quote_source = "Jeweller Specified Manual Cost"
            else:
                quote = LicensedDiamondService.get_pricing_quote({
                    "carat": float(diamond_carat),
                    "color": diamond_color,
                    "clarity": diamond_clarity,
                    "cut": diamond_cut,
                    "shape": diamond_shape,
                    "origin_type": diamond_origin,
                    "report_number": diamond_report_no
                })
                diamond_cost = Decimal(str(quote.get("total_wholesale_inr", 0))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                diamond_rate_per_ct = Decimal(str(quote.get("price_per_carat_inr", 0))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                diamond_quote_source = quote.get("source", "Wholesale Benchmark")

            diamond_label = f"{diamond_cert} ({diamond_carat} ct, {diamond_stones} stone{'s' if diamond_stones > 1 else ''})"
            diamond_sub = f"{diamond_origin} • {diamond_color} / {diamond_clarity} / {diamond_cut}"
        else:
            diamond_carat = Decimal("0.00")
            diamond_stones = 0
            diamond_cost = Decimal("0.00")
            diamond_rate_per_ct = Decimal("0.00")
            diamond_color = "N/A"
            diamond_clarity = "N/A"
            diamond_cut = "N/A"
            diamond_shape = "N/A"
            diamond_origin = "N/A"
            diamond_cert = "None"
            diamond_report_no = ""
            diamond_quote_source = "None"
            diamond_label = "No Diamond"
            diamond_sub = ""

        # 3. Gemstones (Ruby, Emerald, Sapphire, etc.)
        raw_gem_cost = params.get("gem_cost") if params.get("gem_cost") is not None else params.get("gemstone_cost", 0.0)
        gem_carat_raw = params.get("gem_carat") if params.get("gem_carat") is not None else params.get("gemstone_carat", 0.0)
        gem_carat = Decimal(str(max(0.0, float(gem_carat_raw or 0.0))))
        gem_rate_raw = params.get("gem_rate_per_carat") or params.get("gem_rate") or params.get("ruby_rate_per_carat")

        if gem_rate_raw and float(gem_rate_raw) > 0 and gem_carat > 0:
            gem_rate_per_ct = Decimal(str(float(gem_rate_raw))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            gem_cost = (gem_carat * gem_rate_per_ct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        elif raw_gem_cost is not None and float(raw_gem_cost) > 0:
            gem_cost = Decimal(str(float(raw_gem_cost))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            gem_rate_per_ct = (gem_cost / gem_carat).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if gem_carat > 0 else Decimal("0.00")
        else:
            gem_cost = Decimal("0.00")
            gem_rate_per_ct = Decimal("0.00")

        raw_enable_gem = params.get("enable_gemstone")
        if isinstance(raw_enable_gem, str):
            enable_gemstone = raw_enable_gem.lower() in ("true", "1", "yes", "on")
        elif raw_enable_gem is not None:
            enable_gemstone = bool(raw_enable_gem)
        else:
            enable_gemstone = bool(gem_cost > Decimal("0.00") or gem_carat > Decimal("0.00"))

        gem_type = str(params.get("gem_type", "Ruby (Manik)")).strip()
        gem_origin = str(params.get("gem_origin", "Burma (Myanmar)")).strip()
        gem_treatment = str(params.get("gem_treatment", "Natural Unheated")).strip()
        gem_label = f"{gem_type} Gemstone ({gem_carat} ct)" if enable_gemstone and gem_carat > 0 else "No Gemstone"

        # 4. Making, Setting & Labour Charges
        making_mode = str(params.get("making_mode", "per_gram")).strip()
        raw_making = params.get("making_val") if params.get("making_val") is not None else (params.get("making_charge_per_gram") or params.get("making_rate", 0.0))
        making_val = Decimal(str(max(0.0, float(raw_making))))

        if making_mode == "per_gram":
            making_charge = (gross_weight * making_val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        elif making_mode == "percentage":
            making_charge = (metal_cost * (making_val / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            making_charge = making_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        setting_mode = str(params.get("setting_mode", "per_stone")).strip()
        setting_val = Decimal(str(max(0.0, float(params.get("setting_val", 0.0)))))
        if setting_mode == "per_stone":
            setting_charge = (Decimal(str(diamond_stones)) * setting_val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            setting_charge = setting_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        raw_hallmark = params.get("hallmark_fee") if params.get("hallmark_fee") is not None else params.get("hallmarking_fee", 45.0)
        hallmark_fee = Decimal(str(max(0.0, float(raw_hallmark)))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        misc_labour = Decimal(str(max(0.0, float(params.get("misc_labour", 0.0))))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total_making_setting = (making_charge + setting_charge).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_hallmark_labour = (hallmark_fee + misc_labour).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_artisan_labour = (total_making_setting + total_hallmark_labour).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 5. Total Landed Cost (CP)
        landed_cost = (
            metal_cost +
            diamond_cost +
            (gem_cost if enable_gemstone else Decimal("0.00")) +
            making_charge +
            setting_charge +
            hallmark_fee +
            misc_labour
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 6. Commercial Strategy (Markup & Discount)
        raw_markup = params.get("markup_pct") if params.get("markup_pct") is not None else params.get("retail_markup_pct", 25.0)
        markup_pct = Decimal(str(max(0.0, float(raw_markup))))
        retail_pre_discount = (landed_cost * (Decimal("1.0") + (markup_pct / Decimal("100")))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        discount_mode = str(params.get("discount_mode", "percentage")).strip()
        raw_discount = params.get("discount_val") if params.get("discount_val") is not None else params.get("discount_pct", 0.0)
        discount_val = Decimal(str(max(0.0, float(raw_discount))))
        if discount_mode == "percentage":
            discount_amount = (retail_pre_discount * (discount_val / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            discount_amount = min(discount_val, retail_pre_discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Net Taxable Retail Amount
        taxable_amount = max(Decimal("0.00"), retail_pre_discount - discount_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 7. Indian GST Calculation (HSN 7113 - 3.0%)
        is_interstate = bool(params.get("is_interstate", False))
        if isinstance(params.get("is_interstate"), str):
            is_interstate = params.get("is_interstate").lower() in ("true", "1", "yes")

        gst_rate = Decimal(str(float(params.get("gst_rate", 3.0))))

        if is_interstate:
            igst_amount = (taxable_amount * (gst_rate / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            cgst_amount = Decimal("0.00")
            sgst_amount = Decimal("0.00")
            total_gst = igst_amount
        else:
            half_rate = gst_rate / Decimal("2")
            cgst_amount = (taxable_amount * (half_rate / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            sgst_amount = (taxable_amount * (half_rate / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            igst_amount = Decimal("0.00")
            total_gst = (cgst_amount + sgst_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Grand Total Payable
        grand_total = (taxable_amount + total_gst).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 8. Realized Jeweller Gross Profit & Margins
        profit_amount = (taxable_amount - landed_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if taxable_amount > Decimal("0.00"):
            margin_pct = ((profit_amount / taxable_amount) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        else:
            margin_pct = Decimal("0.0")

        if landed_cost > Decimal("0.00"):
            realized_markup_pct = ((profit_amount / landed_cost) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        else:
            realized_markup_pct = Decimal("0.0")

        # 9. Build Structured Itemized Line Items for Tally/e-Invoice Bill Table
        # (Exact columns: Sl No, Description of Goods, HSN/SAC, Quantity, Rate, per, Disc. %, Amount)
        line_items: List[Dict[str, Any]] = []
        sr_idx = 1

        # Calculate proportional retail share of each component if retail markup exists
        cost_ratio = (taxable_amount / landed_cost) if landed_cost > 0 else Decimal("1.0")

        # Metal Item (Gold / Silver / Platinum)
        if gross_weight > Decimal("0.000"):
            retail_metal_amt = (metal_cost * cost_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            effective_metal_rate = (retail_metal_amt / gross_weight).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if gross_weight > 0 else metal_rate_per_g
            metal_hsn = "7113"
            metal_desc_title = f"{purity} Hallmarked {metal_category} Jewellery"
            metal_spec = f"Purity: {purity} • Net Wt: {net_weight:.3f}g • Gross Wt: {gross_weight:.3f}g"
            if wastage_pct > 0:
                metal_spec += f" (incl. {wastage_pct}% Wastage)"

            line_items.append({
                "sr": sr_idx,
                "title": metal_desc_title,
                "description": metal_desc_title,
                "specifications": metal_spec,
                "hsn": metal_hsn,
                "quantity": f"{gross_weight:.3f} g",
                "rate": float(effective_metal_rate),
                "formatted_rate": f"{effective_metal_rate:,.2f}",
                "per": "g",
                "disc_pct": float(discount_val) if discount_mode == "percentage" else 0.0,
                "disc_pct_str": f"{discount_val:.2f}%" if (discount_mode == "percentage" and discount_val > 0) else "",
                "amount": float(retail_metal_amt),
                "formatted_amount": f"{retail_metal_amt:,.2f}"
            })
            sr_idx += 1

        # Diamond Item
        if enable_diamond and diamond_carat > Decimal("0.00"):
            retail_dia_amt = (diamond_cost * cost_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            effective_dia_rate = (retail_dia_amt / diamond_carat).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if diamond_carat > 0 else diamond_rate_per_ct
            dia_hsn = "7102"
            dia_title = f"{diamond_origin} Diamond Solitaire ({diamond_carat:.2f} ct)"
            dia_spec = f"Shape: {diamond_shape} • Color: {diamond_color} • Clarity: {diamond_clarity} • Cut: {diamond_cut}"
            if diamond_report_no:
                dia_spec += f" • Cert: {diamond_cert} #{diamond_report_no}"
            else:
                dia_spec += f" • Cert: {diamond_cert}"

            line_items.append({
                "sr": sr_idx,
                "title": dia_title,
                "description": dia_title,
                "specifications": dia_spec,
                "hsn": dia_hsn,
                "quantity": f"{diamond_carat:.2f} ct",
                "rate": float(effective_dia_rate),
                "formatted_rate": f"{effective_dia_rate:,.2f}",
                "per": "ct",
                "disc_pct": float(discount_val) if discount_mode == "percentage" else 0.0,
                "disc_pct_str": f"{discount_val:.2f}%" if (discount_mode == "percentage" and discount_val > 0) else "",
                "amount": float(retail_dia_amt),
                "formatted_amount": f"{retail_dia_amt:,.2f}"
            })
            sr_idx += 1

        # Gemstone / Ruby Item
        if enable_gemstone and (gem_carat > Decimal("0.00") or gem_cost > Decimal("0.00")):
            retail_gem_amt = (gem_cost * cost_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            effective_gem_rate = (retail_gem_amt / gem_carat).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if gem_carat > 0 else gem_rate_per_ct
            gem_hsn = "7103"
            gem_title = f"Natural {gem_type} ({gem_carat:.2f} ct)"
            gem_spec = f"Origin: {gem_origin} • Treatment: {gem_treatment}"

            line_items.append({
                "sr": sr_idx,
                "title": gem_title,
                "description": gem_title,
                "specifications": gem_spec,
                "hsn": gem_hsn,
                "quantity": f"{gem_carat:.2f} ct",
                "rate": float(effective_gem_rate),
                "formatted_rate": f"{effective_gem_rate:,.2f}",
                "per": "ct",
                "disc_pct": float(discount_val) if discount_mode == "percentage" else 0.0,
                "disc_pct_str": f"{discount_val:.2f}%" if (discount_mode == "percentage" and discount_val > 0) else "",
                "amount": float(retail_gem_amt),
                "formatted_amount": f"{retail_gem_amt:,.2f}"
            })
            sr_idx += 1

        # Making & Setting Charges Item
        if total_artisan_labour > Decimal("0.00"):
            retail_labour_amt = (total_artisan_labour * cost_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            labour_hsn = "9988"
            labour_title = "Artisan Making, Stone Setting & Hallmarking"
            labour_spec = f"Goldsmith benchmark crafting & finishing • BIS Hallmarking Fee ₹{hallmark_fee}"

            line_items.append({
                "sr": sr_idx,
                "title": labour_title,
                "description": labour_title,
                "specifications": labour_spec,
                "hsn": labour_hsn,
                "quantity": "1 Job",
                "rate": float(retail_labour_amt),
                "formatted_rate": f"{retail_labour_amt:,.2f}",
                "per": "Job",
                "disc_pct": 0.0,
                "disc_pct_str": "",
                "amount": float(retail_labour_amt),
                "formatted_amount": f"{retail_labour_amt:,.2f}"
            })
            sr_idx += 1

        # If line items sum has minor rounding difference with taxable_amount, adjust the primary line item
        if line_items:
            sum_line_items = sum(Decimal(str(item["amount"])) for item in line_items)
            diff = taxable_amount - sum_line_items
            if abs(diff) > Decimal("0.00"):
                line_items[0]["amount"] = float(Decimal(str(line_items[0]["amount"])) + diff)
                line_items[0]["formatted_amount"] = f"{line_items[0]['amount']:,.2f}"

        # 10. Build HSN/SAC Tax Breakdown Table
        # Groups by HSN code (e.g. 7113, 7102, 7103, 9988)
        hsn_groups: Dict[str, Decimal] = {}
        for item in line_items:
            h = item["hsn"]
            hsn_groups[h] = hsn_groups.get(h, Decimal("0.00")) + Decimal(str(item["amount"]))

        hsn_summary: List[Dict[str, Any]] = []
        tot_taxable_hsn = Decimal("0.00")
        tot_central_tax = Decimal("0.00")
        tot_state_tax = Decimal("0.00")
        tot_hsn_tax = Decimal("0.00")

        half_gst = gst_rate / Decimal("2")
        for hsn_code, val in hsn_groups.items():
            tot_taxable_hsn += val
            if is_interstate:
                c_rate = Decimal("0.0")
                c_amt = Decimal("0.00")
                s_rate = Decimal("0.0")
                s_amt = Decimal("0.00")
                tot_tax_row = (val * (gst_rate / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                c_rate = half_gst
                c_amt = (val * (half_gst / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                s_rate = half_gst
                s_amt = (val * (half_gst / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                tot_tax_row = c_amt + s_amt

            tot_central_tax += c_amt
            tot_state_tax += s_amt
            tot_hsn_tax += tot_tax_row

            hsn_summary.append({
                "hsn": hsn_code,
                "taxable_value": float(val),
                "formatted_taxable_value": f"{val:,.2f}",
                "central_tax_rate": f"{c_rate:g}%" if not is_interstate else "0%",
                "central_tax_amount": float(c_amt),
                "formatted_central_tax_amount": f"{c_amt:,.2f}",
                "state_tax_rate": f"{s_rate:g}%" if not is_interstate else "0%",
                "state_tax_amount": float(s_amt),
                "formatted_state_tax_amount": f"{s_amt:,.2f}",
                "integrated_tax_rate": f"{gst_rate:g}%" if is_interstate else "0%",
                "integrated_tax_amount": float(tot_tax_row) if is_interstate else 0.0,
                "total_tax_amount": float(tot_tax_row),
                "formatted_total_tax_amount": f"{tot_tax_row:,.2f}"
            })

        amount_words = cls.number_to_indian_words(int(grand_total), "Indian Rupee ")
        tax_words = cls.number_to_indian_words(int(total_gst), "Indian Rupee ")

        return {
            # Metal
            "metal_type": metal_type,
            "purity": purity,
            "net_weight_grams": float(net_weight),
            "gross_weight_grams": float(gross_weight),
            "wastage_pct": float(wastage_pct),
            "metal_rate_per_g": float(metal_rate_per_g),
            "metal_cost": float(metal_cost),
            "metal_label": metal_label,
            "metal_category": metal_category,
            "formatted_metal_cost": cls.format_inr(metal_cost),

            # Diamond
            "enable_diamond": enable_diamond,
            "diamond_carat": float(diamond_carat),
            "diamond_stones": diamond_stones,
            "diamond_color": diamond_color,
            "diamond_clarity": diamond_clarity,
            "diamond_cut": diamond_cut,
            "diamond_shape": diamond_shape,
            "diamond_origin": diamond_origin,
            "diamond_cert": diamond_cert,
            "diamond_report_no": diamond_report_no,
            "diamond_rate_per_ct": float(diamond_rate_per_ct),
            "diamond_cost": float(diamond_cost),
            "diamond_quote_source": diamond_quote_source,
            "diamond_label": diamond_label,
            "diamond_sub": diamond_sub,
            "formatted_diamond_cost": cls.format_inr(diamond_cost),

            # Gemstone / Ruby
            "enable_gemstone": enable_gemstone,
            "gem_type": gem_type,
            "gem_carat": float(gem_carat),
            "gem_rate_per_ct": float(gem_rate_per_ct),
            "gem_cost": float(gem_cost),
            "gem_origin": gem_origin,
            "gem_treatment": gem_treatment,
            "gem_label": gem_label,
            "formatted_gem_cost": cls.format_inr(gem_cost),

            # Labour & Hallmarking
            "making_mode": making_mode,
            "making_charge": float(making_charge),
            "setting_mode": setting_mode,
            "setting_charge": float(setting_charge),
            "total_making_setting": float(total_making_setting),
            "hallmark_fee": float(hallmark_fee),
            "misc_labour": float(misc_labour),
            "total_hallmark_labour": float(total_hallmark_labour),
            "total_artisan_labour": float(total_artisan_labour),
            "formatted_making_setting": cls.format_inr(total_making_setting),
            "formatted_hallmark_labour": cls.format_inr(total_hallmark_labour),

            # Landed Cost (CP)
            "landed_cost": float(landed_cost),
            "formatted_landed_cost": cls.format_inr(landed_cost),

            # Commercial & Retail (SP)
            "markup_pct": float(markup_pct),
            "retail_pre_discount": float(retail_pre_discount),
            "discount_mode": discount_mode,
            "discount_val": float(discount_val),
            "discount_amount": float(discount_amount),
            "formatted_discount_amount": cls.format_inr(discount_amount),
            "taxable_amount": float(taxable_amount),
            "formatted_taxable_amount": cls.format_inr(taxable_amount),

            # GST
            "gst_rate": float(gst_rate),
            "is_interstate": is_interstate,
            "cgst_amount": float(cgst_amount),
            "sgst_amount": float(sgst_amount),
            "igst_amount": float(igst_amount),
            "total_gst": float(total_gst),
            "formatted_total_gst": cls.format_inr(total_gst),

            # Grand Total
            "grand_total": float(grand_total),
            "formatted_grand_total": cls.format_inr(grand_total),

            # Profit & Margins
            "profit_amount": float(profit_amount),
            "margin_pct": float(margin_pct),
            "realized_markup_pct": float(realized_markup_pct),
            "formatted_profit_amount": cls.format_inr(profit_amount),

            # Words Representation (Matching exact Indian GST Tax Invoice format)
            "amount_in_words": amount_words,
            "amount_chargeable_words": amount_words,
            "tax_amount_words": tax_words,

            # Structured Tally / e-Invoice Bill Line Items & HSN Summary
            "line_items": line_items,
            "hsn_summary": hsn_summary,
            "total_taxable_hsn": float(tot_taxable_hsn),
            "formatted_total_taxable_hsn": f"{tot_taxable_hsn:,.2f}",
            "total_central_tax": float(tot_central_tax),
            "formatted_total_central_tax": f"{tot_central_tax:,.2f}",
            "total_state_tax": float(tot_state_tax),
            "formatted_total_state_tax": f"{tot_state_tax:,.2f}",
            "total_hsn_tax": float(tot_hsn_tax),
            "formatted_total_hsn_tax": f"{tot_hsn_tax:,.2f}",

            # Live Bullions & IBJA Traceability
            "bullions_url": "https://bullions.co.in/",
            "ibja_url": "https://www.ibja.co/",
            "bullion_source": IBJAGoldService.get_current_rates().get("source", "Bullions.co.in Live Market Rates"),
            "bullion_timestamp": IBJAGoldService.get_current_rates().get("fetched_timestamp", ""),
            "bullion_is_stale": IBJAGoldService.get_current_rates().get("is_stale", False),
            "bullion_status": IBJAGoldService.get_current_rates().get("status", "LIVE")
        }

    @classmethod
    def format_inr(cls, value: Any) -> str:
        """Formats a number or Decimal into standard Indian Rupee format."""
        try:
            val_dec = Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            is_neg = val_dec < 0
            val_str = str(abs(val_dec))

            if len(val_str) <= 3:
                res = val_str
            else:
                last_three = val_str[-3:]
                remaining = val_str[:-3]
                parts = []
                while len(remaining) > 2:
                    parts.insert(0, remaining[-2:])
                    remaining = remaining[:-2]
                if remaining:
                    parts.insert(0, remaining)
                res = ",".join(parts) + "," + last_three

            prefix = "-₹ " if is_neg else "₹ "
            return prefix + res
        except Exception:
            return f"₹ {value}"

    @classmethod
    def number_to_indian_words(cls, n: int, currency_prefix: str = "Indian Rupee ") -> str:
        """Converts integer into Indian numbering currency words (Lakhs, Crores)."""
        if n == 0:
            return f"{currency_prefix}Zero Only"

        ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
                "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

        def two_digits(num):
            if num < 20:
                return ones[num]
            else:
                return tens[num // 10] + (" " + ones[num % 10] if num % 10 != 0 else "")

        def three_digits(num):
            h = num // 100
            rem = num % 100
            res = ""
            if h > 0:
                res += ones[h] + " Hundred"
            if rem > 0:
                if res:
                    res += " "
                res += two_digits(rem)
            return res

        crore = n // 10000000
        rem_cr = n % 10000000

        lakh = rem_cr // 100000
        rem_lakh = rem_cr % 100000

        thousand = rem_lakh // 1000
        rem_th = rem_lakh % 1000

        parts = []
        if crore > 0:
            parts.append(two_digits(crore) + " Crore")
        if lakh > 0:
            parts.append(two_digits(lakh) + " Lakh")
        if thousand > 0:
            parts.append(two_digits(thousand) + " Thousand")
        if rem_th > 0:
            parts.append(three_digits(rem_th))

        words = " ".join(parts).strip()
        return f"{currency_prefix}{words} Only"
