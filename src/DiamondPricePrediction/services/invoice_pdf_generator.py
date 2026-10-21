import io
import math
from typing import Dict, Any, Optional, List
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing

from DiamondPricePrediction.services.einvoice_service import EInvoiceService
from DiamondPricePrediction.services.jewellery_calculator import JewelleryCalculator

class InvoicePdfGenerator:
    """
    Official Indian GST e-Invoice PDF Generation Engine (Strictly Black & White).
    
    Generates exact Tally ERP / Indian GST Portal Tax Invoices matching
    statutory Rule 46 requirements:
      - Strictly Black & White typography and crisp solid black borders
      - e-Invoice header with scannable QR Code, 64-char IRN, Ack No, Ack Date
      - 2-Column Seller, Consignee & Buyer KYC / Dispatch Metadata Grid
      - Itemized Jewellery Table (Gold, Silver, Diamond, Ruby, Platinum, Making Charges)
      - Amount Chargeable in Words ("Indian Rupee ... Only") and E. & O.E.
      - Full HSN/SAC Tax Breakup Summary Table (Taxable Value, CGST, SGST, IGST, Total Tax)
      - Tax Amount in Words
      - Statutory Declaration & Authorised Signatory Box
      - Separate Customer View vs Internal Store Audit Copy (with Landed Costs & Margins)
    """

    BLACK = colors.black
    WHITE = colors.white

    @classmethod
    def generate_invoice_pdf(
        cls,
        invoice: Dict[str, Any],
        jeweller_profile: Optional[Dict[str, Any]] = None,
        base_url: str = "http://localhost:8080",
        is_internal: bool = False
    ) -> bytes:
        """
        Builds a crisp, publication-grade Black & White Indian GST Tax Invoice PDF.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=25,
            rightMargin=25,
            topMargin=20,
            bottomMargin=20
        )

        printable_width = 545.0  # 595.27 - 50

        jeweller = jeweller_profile or invoice.get("seller") or {
            "business_name": "GemForecast Fine Jewels",
            "owner_name": "Master Jeweller",
            "city": "Mumbai",
            "address": "Bullion Plaza, Zaveri Bazaar, Mumbai 400002",
            "gst_number": "27AABCG1234F1Z5",
            "email": "billing@gemforecast.com",
            "phone": "+91 98200 11223"
        }

        calc = invoice.get("calc", {})
        if not calc.get("line_items"):
            recalc = JewelleryCalculator.calculate(calc)
            calc.update(recalc)

        seller_gstin = jeweller.get("gst_number") or ""
        buyer_gstin = invoice.get("customer_gstin", "")

        # Retrieve or build full e-Invoice package
        einvoice = invoice.get("einvoice")
        if not einvoice:
            einvoice = EInvoiceService.get_full_einvoice_package(
                supplier_gstin=seller_gstin,
                buyer_gstin=buyer_gstin,
                doc_no=invoice.get("invoice_number", "GF-2026-0001"),
                doc_date_str=invoice.get("invoice_date", "Today"),
                grand_total=invoice.get("grand_total", 0.0),
                taxable_total=invoice.get("taxable_amount", 0.0),
                total_gst=invoice.get("total_gst", 0.0),
                item_count=len(calc.get("line_items", [])) or 1,
                main_hsn=calc.get("line_items", [{}])[0].get("hsn", "7113") if calc.get("line_items") else "7113",
                supplier_name=jeweller.get("business_name", "GemForecast Fine Jewels"),
                buyer_name=invoice.get("customer_name", "Valued Customer"),
                share_token=invoice.get("share_token", ""),
                base_url=base_url
            )

        styles = getSampleStyleSheet()

        # Crisp B&W Paragraph Styles
        style_title = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            alignment=1,  # Center
            textColor=cls.BLACK
        )
        style_einvoice_lbl = ParagraphStyle(
            'EInvoiceLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            alignment=1,  # Center
            textColor=cls.BLACK
        )
        style_irn = ParagraphStyle(
            'IRNText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=6.5,
            leading=8.5,
            textColor=cls.BLACK
        )
        style_irn_bold = ParagraphStyle(
            'IRNTextBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=6.5,
            leading=8.5,
            textColor=cls.BLACK
        )
        style_cell = ParagraphStyle(
            'GridCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.2,
            leading=9.2,
            textColor=cls.BLACK
        )
        style_cell_bold = ParagraphStyle(
            'GridCellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.2,
            leading=9.2,
            textColor=cls.BLACK
        )
        style_th = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.2,
            leading=9.2,
            alignment=0,
            textColor=cls.BLACK
        )
        style_th_right = ParagraphStyle(
            'TableHeaderRight',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.2,
            leading=9.2,
            alignment=2,
            textColor=cls.BLACK
        )
        style_th_center = ParagraphStyle(
            'TableHeaderCenter',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.2,
            leading=9.2,
            alignment=1,
            textColor=cls.BLACK
        )
        style_cell_right = ParagraphStyle(
            'CellRight',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.2,
            leading=9.2,
            alignment=2,
            textColor=cls.BLACK
        )
        style_cell_center = ParagraphStyle(
            'CellCenter',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.2,
            leading=9.2,
            alignment=1,
            textColor=cls.BLACK
        )
        style_footnote = ParagraphStyle(
            'Footnote',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7,
            leading=9,
            alignment=1,
            textColor=cls.BLACK
        )

        elements = []

        # ============================================================
        # 0. OPTIONAL INTERNAL COPY BADGE (FOR JEWELLER STORE AUDIT)
        # ============================================================
        if is_internal:
            internal_banner = ParagraphStyle(
                'InternalBanner',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=8.5,
                leading=11,
                alignment=1,
                textColor=cls.BLACK
            )
            elements.append(Paragraph("** DUPLICATE — STORE / INTERNAL AUDIT COPY (CONFIDENTIAL) **", internal_banner))
            elements.append(Spacer(1, 4))

        # ============================================================
        # 1. TOP HEADER: Adaptive Rule 46 Tax Invoice or Rule 48(4) e-Invoice
        # ============================================================
        seller_state = einvoice.get("seller_state", "Maharashtra")
        seller_code = einvoice.get("seller_state_code", "27")
        buyer_state = einvoice.get("buyer_state", "Maharashtra")
        buyer_code = einvoice.get("buyer_state_code", "27")

        qr_drawing = EInvoiceService.generate_qr_drawing(einvoice["qr_payload"], size=62.0)
        is_irn_registered = bool(einvoice.get("is_irn_registered"))

        if is_irn_registered:
            left_header_html = f"""
            <b>IRN &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:</b> {einvoice.get('irn_line1', '')}-<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{einvoice.get('irn_line2', '')}<br/>
            <b>Ack No. &nbsp;:</b> {einvoice.get('ack_no', '')}<br/>
            <b>Ack Date:</b> {einvoice.get('ack_date', '')}
            """
            center_header_html = "<b>Tax Invoice</b>"
            right_header_label = "<b>e-Invoice</b>"
            top_col_widths = [315.0, 150.0, 80.0]
        else:
            left_header_html = f"""
            <b>Invoice No. &nbsp;:</b> {invoice.get('invoice_number', 'GF-2026-0001')}<br/>
            <b>Invoice Date:</b> {einvoice.get('ack_date', invoice.get('invoice_date', 'Today'))}<br/>
            <b>Place of Supply:</b> {buyer_state} ({buyer_code})<br/>
            <b>Reverse Charge:</b> No
            """
            center_header_html = """
            <b>TAX INVOICE</b><br/>
            <font size="6.5">(Issued under Rule 46 of CGST Rules, 2017)</font><br/>
            <font size="6.5"><b>ORIGINAL FOR RECIPIENT</b></font>
            """
            right_header_label = "<b>Digital Verification</b>"
            top_col_widths = [240.0, 220.0, 85.0]

        top_header_table = Table([
            [
                Paragraph(left_header_html, style_irn),
                Paragraph(center_header_html, style_title),
                [Paragraph(right_header_label, style_einvoice_lbl), qr_drawing]
            ]
        ], colWidths=top_col_widths)
        top_header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(top_header_table)
        elements.append(Spacer(1, 4))

        # ============================================================
        # 2. SELLER, BUYER & DISPATCH METADATA GRID
        # ============================================================
        cust_name = invoice.get("customer_name", "Valued Client")
        cust_addr = invoice.get("customer_address", "In-Store Counter Purchase")
        cust_gst = buyer_gstin if buyer_gstin else "Unregistered"
        cust_pan = invoice.get("customer_pan", "")

        seller_name = jeweller.get('business_name', 'GemForecast Fine Jewels')
        seller_addr = jeweller.get('address') or jeweller.get('city') or 'Store Counter'
        seller_gst_val = seller_gstin if seller_gstin else "Unregistered"

        seller_text = f"""
        <b>{seller_name}</b><br/>
        {seller_addr}<br/>
        GSTIN/UIN: <b>{seller_gst_val}</b><br/>
        State Name : <b>{seller_state}</b>, Code : <b>{seller_code}</b>
        """

        consignee_text = f"""
        <b>Consignee (Ship to)</b><br/>
        <b>{cust_name}</b><br/>
        {cust_addr}<br/>
        GSTIN/UIN &nbsp;&nbsp;: <b>{cust_gst}</b><br/>
        State Name &nbsp;: <b>{buyer_state}</b>, Code : <b>{buyer_code}</b>
        """

        buyer_text = f"""
        <b>Buyer (Bill to)</b><br/>
        <b>{cust_name}</b><br/>
        {cust_addr}<br/>
        GSTIN/UIN &nbsp;&nbsp;: <b>{cust_gst}</b>{" | PAN: <b>" + cust_pan + "</b>" if cust_pan else ""}<br/>
        State Name &nbsp;: <b>{buyer_state}</b>, Code : <b>{buyer_code}</b>
        """

        inv_num = invoice.get("invoice_number", "GF-2026-0001")
        inv_date = einvoice.get("ack_date", invoice.get("invoice_date", "Today"))
        dispatch = invoice.get("dispatch", {})

        # Right side dispatch subtable rows
        col_w_half = printable_width / 2.0  # 272.5 pt
        r_sub_w = col_w_half / 2.0         # 136.25 pt

        right_dispatch_table = Table([
            [
                Paragraph(f"Invoice No.<br/><b>{inv_num}</b>", style_cell),
                Paragraph(f"Dated<br/><b>{inv_date}</b>", style_cell)
            ],
            [
                Paragraph(f"Delivery Note<br/>{dispatch.get('delivery_note', '')}", style_cell),
                Paragraph(f"Mode/Terms of Payment<br/><b>{dispatch.get('mode_terms_of_payment', 'Immediate')}</b>", style_cell)
            ],
            [
                Paragraph(f"Reference No. &amp; Date.<br/>{dispatch.get('reference_no_date', '')}", style_cell),
                Paragraph(f"Other References<br/>{dispatch.get('other_references', '')}", style_cell)
            ],
            [
                Paragraph(f"Buyer's Order No.<br/>{dispatch.get('buyer_order_no', '')}", style_cell),
                Paragraph(f"Dated<br/>{dispatch.get('order_dated', '')}", style_cell)
            ],
            [
                Paragraph(f"Dispatch Doc No.<br/>{dispatch.get('dispatch_doc_no', '')}", style_cell),
                Paragraph(f"Delivery Note Date<br/>{dispatch.get('delivery_note_date', '')}", style_cell)
            ],
            [
                Paragraph(f"Dispatched through<br/>{dispatch.get('dispatched_through', 'Store Counter')}", style_cell),
                Paragraph(f"Destination<br/>{dispatch.get('destination', 'Mumbai')}", style_cell)
            ],
            [
                Paragraph(f"Terms of Delivery<br/>{dispatch.get('terms_of_delivery', 'Certified BIS Hallmarked Jewellery.')}", style_cell),
                ""
            ]
        ], colWidths=[r_sub_w, r_sub_w])

        right_dispatch_table.setStyle(TableStyle([
            ('SPAN', (0, 6), (1, 6)),  # Span Terms of Delivery across both columns
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BLACK),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BLACK),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))

        left_party_table = Table([
            [Paragraph(seller_text, style_cell)],
            [Paragraph(consignee_text, style_cell)],
            [Paragraph(buyer_text, style_cell)]
        ], colWidths=[col_w_half])

        left_party_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BLACK),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BLACK),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))

        two_col_master_table = Table([
            [left_party_table, right_dispatch_table]
        ], colWidths=[col_w_half, col_w_half])

        two_col_master_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(two_col_master_table)

        # ============================================================
        # 3. LINE ITEMS TABLE (Exact columns from attached Indian bill)
        # Sl No. | Description of Goods | HSN/SAC | Quantity | Rate | per | Disc. % | Amount
        # ============================================================
        # Col widths: 22, 215, 45, 53, 58, 27, 35, 90 = 545 pt
        items_cols = [22.0, 215.0, 45.0, 53.0, 58.0, 27.0, 35.0, 90.0]

        items_table_data = [
            [
                Paragraph("<b>Sl<br/>No.</b>", style_th_center),
                Paragraph("<b>Description of Goods</b>", style_th),
                Paragraph("<b>HSN/SAC</b>", style_th_center),
                Paragraph("<b>Quantity</b>", style_th_center),
                Paragraph("<b>Rate</b>", style_th_right),
                Paragraph("<b>per</b>", style_th_center),
                Paragraph("<b>Disc. %</b>", style_th_center),
                Paragraph("<b>Amount</b>", style_th_right)
            ]
        ]

        raw_items = calc.get("line_items", [])
        total_qty_str = ""
        qtys = []

        for idx, item in enumerate(raw_items, 1):
            title = item.get("title") or item.get("description", "Jewellery Article")
            spec = item.get("specifications", "")
            desc_html = f"<b>{title}</b>"
            if spec:
                desc_html += f"<br/><font size='6.5' color='#000000'>{spec}</font>"

            qty_val = item.get("quantity", "")
            if qty_val:
                qtys.append(qty_val)

            items_table_data.append([
                Paragraph(str(idx), style_cell_center),
                Paragraph(desc_html, style_cell),
                Paragraph(str(item.get("hsn", "7113")), style_cell_center),
                Paragraph(str(qty_val), style_cell_center),
                Paragraph(f"{item.get('formatted_rate', item.get('rate', ''))}", style_cell_right),
                Paragraph(str(item.get("per", "g")), style_cell_center),
                Paragraph(str(item.get("disc_pct_str", "")), style_cell_center),
                Paragraph(f"{item.get('formatted_amount', item.get('amount', ''))}", style_cell_right)
            ])

        # If items table has empty rows to match classic Tally height
        # Add internal CGST and SGST line rows inside table (like attached image)
        is_interstate = calc.get("is_interstate", False)
        if is_interstate:
            igst_amt = calc.get("igst_amount", 0.0)
            items_table_data.append([
                "",
                Paragraph("<b><i>IGST</i></b>", style_cell_right),
                "", "", "", "", "",
                Paragraph(f"<b>{igst_amt:,.2f}</b>", style_cell_right)
            ])
        else:
            cgst_amt = calc.get("cgst_amount", 0.0)
            sgst_amt = calc.get("sgst_amount", 0.0)
            items_table_data.append([
                "",
                Paragraph("<b><i>CGST</i></b>", style_cell_right),
                "", "", "", "", "",
                Paragraph(f"<b>{cgst_amt:,.2f}</b>", style_cell_right)
            ])
            items_table_data.append([
                "",
                Paragraph("<b><i>SGST</i></b>", style_cell_right),
                "", "", "", "", "",
                Paragraph(f"<b>{sgst_amt:,.2f}</b>", style_cell_right)
            ])

        # Final Total Row
        grand_tot = calc.get("grand_total", invoice.get("grand_total", 0.0))
        # Dynamically adapt total summary quantity: filter out Job / service units and show actual physical units
        physical_qtys = [q for q in qtys if not q.endswith("Job")]
        summary_qty = " + ".join(physical_qtys) if physical_qtys else (" / ".join(qtys[:2]) if qtys else "")
        items_table_data.append([
            "",
            Paragraph("<b>Total</b>", style_cell_right),
            "",
            Paragraph(f"<b>{summary_qty}</b>", style_cell_center),
            "",
            "",
            "",
            Paragraph(f"<b>₹ {grand_tot:,.2f}</b>", style_cell_right)
        ])

        goods_table = Table(items_table_data, colWidths=items_cols)
        goods_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BLACK),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BLACK),
            ('LINEBELOW', (0, 0), (-1, 0), 1.0, cls.BLACK),  # Header underline
            ('LINEABOVE', (0, -1), (-1, -1), 1.0, cls.BLACK), # Total line top
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(goods_table)

        # ============================================================
        # 4. AMOUNT CHARGEABLE IN WORDS & E. & O.E
        # ============================================================
        words_text = calc.get("amount_chargeable_words", calc.get("amount_in_words", "Indian Rupee Zero Only"))
        amount_words_table = Table([
            [
                Paragraph("Amount Chargeable (in words)", style_cell),
                Paragraph("<i>E. &amp; O.E</i>", style_cell_right)
            ],
            [
                Paragraph(f"<b>{words_text}</b>", style_cell_bold),
                ""
            ]
        ], colWidths=[450.0, 95.0])
        amount_words_table.setStyle(TableStyle([
            ('SPAN', (0, 1), (1, 1)),
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BLACK),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(amount_words_table)

        # ============================================================
        # 5. HSN/SAC TAX BREAKUP TABLE (Matches attached Indian bill)
        # HSN/SAC | Taxable Value | Central Tax (Rate, Amount) | State Tax (Rate, Amount) | Total Tax Amount
        # ============================================================
        hsn_cols = [85.0, 100.0, 50.0, 75.0, 50.0, 75.0, 110.0]

        hsn_table_data = [
            # Two-tier header
            [
                Paragraph("<b>HSN/SAC</b>", style_th_center),
                Paragraph("<b>Taxable<br/>Value</b>", style_th_right),
                Paragraph("<b>Central Tax</b>", style_th_center),
                "",
                Paragraph("<b>State Tax</b>" if not is_interstate else "<b>Integrated Tax</b>", style_th_center),
                "",
                Paragraph("<b>Total<br/>Tax Amount</b>", style_th_right)
            ],
            [
                "",
                "",
                Paragraph("<b>Rate</b>", style_th_center),
                Paragraph("<b>Amount</b>", style_th_right),
                Paragraph("<b>Rate</b>", style_th_center),
                Paragraph("<b>Amount</b>", style_th_right),
                ""
            ]
        ]

        hsn_rows = calc.get("hsn_summary", [])
        if not hsn_rows:
            # Fallback single row for 7113
            taxable_val = calc.get("taxable_amount", 0.0)
            cgst_val = calc.get("cgst_amount", 0.0)
            sgst_val = calc.get("sgst_amount", 0.0)
            hsn_rows = [{
                "hsn": "7113",
                "formatted_taxable_value": f"{taxable_val:,.2f}",
                "central_tax_rate": "1.5%",
                "formatted_central_tax_amount": f"{cgst_val:,.2f}",
                "state_tax_rate": "1.5%",
                "formatted_state_tax_amount": f"{sgst_val:,.2f}",
                "formatted_total_tax_amount": f"{cgst_val + sgst_val:,.2f}"
            }]

        for h in hsn_rows:
            hsn_table_data.append([
                Paragraph(str(h.get("hsn", "7113")), style_cell_center),
                Paragraph(str(h.get("formatted_taxable_value", "")), style_cell_right),
                Paragraph(str(h.get("central_tax_rate", "1.5%")), style_cell_center),
                Paragraph(str(h.get("formatted_central_tax_amount", "0.00")), style_cell_right),
                Paragraph(str(h.get("state_tax_rate", "1.5%")), style_cell_center),
                Paragraph(str(h.get("formatted_state_tax_amount", "0.00")), style_cell_right),
                Paragraph(str(h.get("formatted_total_tax_amount", "0.00")), style_cell_right)
            ])

        # Summary Total row
        tot_taxable_str = calc.get("formatted_total_taxable_hsn", f"{calc.get('taxable_amount', 0.0):,.2f}")
        tot_c_str = calc.get("formatted_total_central_tax", f"{calc.get('cgst_amount', 0.0):,.2f}")
        tot_s_str = calc.get("formatted_total_state_tax", f"{calc.get('sgst_amount', 0.0):,.2f}")
        tot_tax_str = calc.get("formatted_total_hsn_tax", f"{calc.get('total_gst', 0.0):,.2f}")

        hsn_table_data.append([
            Paragraph("<b>Total</b>", style_cell_center),
            Paragraph(f"<b>{tot_taxable_str}</b>", style_cell_right),
            "",
            Paragraph(f"<b>{tot_c_str}</b>", style_cell_right),
            "",
            Paragraph(f"<b>{tot_s_str}</b>", style_cell_right),
            Paragraph(f"<b>{tot_tax_str}</b>", style_cell_right)
        ])

        hsn_table = Table(hsn_table_data, colWidths=hsn_cols)
        hsn_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (0, 1)),  # Span HSN/SAC vertically
            ('SPAN', (1, 0), (1, 1)),  # Span Taxable Value vertically
            ('SPAN', (2, 0), (3, 0)),  # Span Central Tax horizontally
            ('SPAN', (4, 0), (5, 0)),  # Span State Tax horizontally
            ('SPAN', (6, 0), (6, 1)),  # Span Total Tax vertically
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BLACK),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BLACK),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(hsn_table)

        # Tax Amount in words
        tax_words = calc.get("tax_amount_words", "Indian Rupee Zero Only")
        tax_words_table = Table([
            [Paragraph(f"<b>Tax Amount (in words) : {tax_words}</b>", style_cell)]
        ], colWidths=[printable_width])
        tax_words_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BLACK),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(tax_words_table)

        # ============================================================
        # 6. STATUTORY DECLARATION & AUTHORISED SIGNATORY
        # ============================================================
        decl_text = """
        <b>Declaration</b><br/>
        We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.
        """
        biz_name = jeweller.get('business_name', 'Shree Ganesh Gems & Jewels')
        sign_text = f"""
        for <b>{biz_name}</b><br/><br/><br/>
        <div align='right'>Authorised Signatory</div>
        """

        decl_table = Table([
            [
                Paragraph(decl_text, style_cell),
                Paragraph(sign_text, style_cell)
            ]
        ], colWidths=[col_w_half, col_w_half])
        decl_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BLACK),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BLACK),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(decl_table)
        elements.append(Spacer(1, 4))

        # Computer generated invoice note
        elements.append(Paragraph("This is a Computer Generated Invoice", style_footnote))

        # ============================================================
        # 7. INTERNAL JEWELLER STORE AUDIT BREAKDOWN (IF INTERNAL COPY)
        # ============================================================
        if is_internal:
            elements.append(Spacer(1, 10))
            audit_header = ParagraphStyle(
                'AuditHeader',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=8.5,
                leading=11,
                textColor=cls.BLACK
            )
            elements.append(Paragraph("<b>CONFIDENTIAL JEWELLER STORE AUDIT &amp; MARGIN RECORD</b>", audit_header))
            elements.append(Spacer(1, 3))

            audit_data = [
                [
                    Paragraph("<b>Cost Component (CP)</b>", style_th),
                    Paragraph("<b>Acquisition Cost</b>", style_th_right),
                    Paragraph("<b>Commercial Metric</b>", style_th),
                    Paragraph("<b>Value</b>", style_th_right)
                ],
                [
                    Paragraph("Pure Metal Acquisition (Gold/Silver/Pt)", style_cell),
                    Paragraph(f"₹ {calc.get('metal_cost', 0.0):,.2f}", style_cell_right),
                    Paragraph("Retail Markup Applied", style_cell),
                    Paragraph(f"{calc.get('markup_pct', 0.0)}%", style_cell_right)
                ],
                [
                    Paragraph("Diamond Wholesale Acquisition", style_cell),
                    Paragraph(f"₹ {calc.get('diamond_cost', 0.0):,.2f}", style_cell_right),
                    Paragraph("Trade / Festive Discount", style_cell),
                    Paragraph(f"-₹ {calc.get('discount_amount', 0.0):,.2f}", style_cell_right)
                ],
                [
                    Paragraph("Gemstone / Ruby Acquisition", style_cell),
                    Paragraph(f"₹ {calc.get('gem_cost', 0.0):,.2f}", style_cell_right),
                    Paragraph("Net Selling Price (SP)", style_cell),
                    Paragraph(f"₹ {calc.get('taxable_amount', 0.0):,.2f}", style_cell_right)
                ],
                [
                    Paragraph("Artisan Goldsmith Making & Setting Labour", style_cell),
                    Paragraph(f"₹ {calc.get('total_making_setting', 0.0):,.2f}", style_cell_right),
                    Paragraph("<b>Realized Gross Profit</b>", style_cell_bold),
                    Paragraph(f"<b>+₹ {calc.get('profit_amount', 0.0):,.2f}</b>", style_cell_right)
                ],
                [
                    Paragraph("<b>Total Landed Acquisition Cost (CP)</b>", style_cell_bold),
                    Paragraph(f"<b>₹ {calc.get('landed_cost', 0.0):,.2f}</b>", style_cell_right),
                    Paragraph("<b>Gross Profit Margin %</b>", style_cell_bold),
                    Paragraph(f"<b>{calc.get('margin_pct', 0.0)}%</b>", style_cell_right)
                ]
            ]
            audit_table = Table(audit_data, colWidths=[150.0, 122.5, 150.0, 122.5])
            audit_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.5, cls.BLACK),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, cls.BLACK),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(audit_table)

        # Build document
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
