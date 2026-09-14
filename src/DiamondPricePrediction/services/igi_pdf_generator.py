import io
import math
from typing import Dict, Any
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Group, Circle, Polygon
from reportlab.graphics.barcode import qr

class IGIPdfGenerator:
    """
    High-precision authentic IGI Diamond Certificate PDF rendering engine.
    Generates pixel-perfect 3-panel landscape official IGI report PDFs.
    """

    NAVY = colors.HexColor("#081C38")
    GOLD = colors.HexColor("#C5A059")
    DARK_BLUE = colors.HexColor("#0D2C54")
    LIGHT_BG = colors.HexColor("#F4F6F9")
    BORDER_COLOR = colors.HexColor("#CBD5E1")
    TEXT_DARK = colors.HexColor("#1E293B")
    TEXT_MUTED = colors.HexColor("#64748B")

    @classmethod
    def generate_pdf(cls, diamond_spec: Dict[str, Any]) -> bytes:
        """
        Builds a landscape PDF byte stream representing the exact original IGI certificate layout.
        """
        buffer = io.BytesIO()
        # Letter landscape: 792 x 612 pt
        page_width, page_height = landscape(letter)
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        c.setTitle(f"IGI Certificate #{diamond_spec.get('report_number', 'REPORT')}")

        # 1. Background & Border Framework
        c.setFillColor(cls.LIGHT_BG)
        c.rect(0, 0, page_width, page_height, fill=True, stroke=False)

        # Outer decorative frame
        c.setStrokeColor(cls.NAVY)
        c.setLineWidth(3)
        c.rect(15, 15, page_width - 30, page_height - 30)

        c.setStrokeColor(cls.GOLD)
        c.setLineWidth(1)
        c.rect(19, 19, page_width - 38, page_height - 38)

        # 2. Main Top Header Banner
        header_height = 60
        header_y = page_height - 19 - header_height

        c.setFillColor(cls.NAVY)
        c.rect(20, header_y, page_width - 40, header_height, fill=True, stroke=False)

        # Gold accent stripe under header
        c.setFillColor(cls.GOLD)
        c.rect(20, header_y - 4, page_width - 40, 4, fill=True, stroke=False)

        # IGI Logo Text
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(35, header_y + 32, "INTERNATIONAL GEMOLOGICAL INSTITUTE")

        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(cls.GOLD)
        c.drawString(35, header_y + 14, "OFFICIAL GEMOLOGICAL REPORT & CERTIFICATION DOSSIER")

        # Report Number & Date on right side of header
        rep_no = str(diamond_spec.get("report_number", "584392810"))
        rep_date = diamond_spec.get("report_date", "November 18, 2024")
        origin_type = diamond_spec.get("origin_type", "Natural").upper()

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(page_width - 35, header_y + 32, f"IGI REPORT #{rep_no}")

        c.setFont("Helvetica", 10)
        c.drawRightString(page_width - 35, header_y + 14, f"Date: {rep_date} | Origin: {origin_type}")

        # 3. Three Main Vertical Columns (Panels)
        col_y = 30
        col_height = header_y - col_y - 12
        col_width = (page_width - 40 - 24) / 3 # ~242 pt each

        col1_x = 24
        col2_x = col1_x + col_width + 12
        col3_x = col2_x + col_width + 12

        # Draw Panel Backgrounds
        for cx in [col1_x, col2_x, col3_x]:
            c.setFillColor(colors.white)
            c.setStrokeColor(cls.BORDER_COLOR)
            c.setLineWidth(1)
            c.roundRect(cx, col_y, col_width, col_height, 6, fill=True, stroke=True)

        # -------------------------------------------------------------
        # PANEL 1: PRIMARY IGI DIAMOND GRADING RESULTS (4Cs)
        # -------------------------------------------------------------
        cls._render_panel_header(c, col1_x, col_y + col_height - 28, col_width, "1. IGI GRADING RESULTS")

        curr_y = col_y + col_height - 48
        
        # Report Title
        report_type = diamond_spec.get("report_type", f"IGI {origin_type.title()} Diamond Report")
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(cls.NAVY)
        c.drawString(col1_x + 12, curr_y, report_type)
        curr_y -= 22

        # Specs grid
        specs_col1 = [
            ("Shape and Cutting Style", diamond_spec.get("shape", "Round Brilliant")),
            ("Carat Weight", f"{diamond_spec.get('carat', 1.00):.2f} Carat"),
            ("Color Grade", str(diamond_spec.get("color", "F"))),
            ("Clarity Grade", str(diamond_spec.get("clarity", "VS1"))),
            ("Cut Grade", str(diamond_spec.get("cut", "Ideal"))),
        ]

        for label, val in specs_col1:
            c.setFont("Helvetica", 9)
            c.setFillColor(cls.TEXT_MUTED)
            c.drawString(col1_x + 12, curr_y, label)
            
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(cls.TEXT_DARK)
            c.drawRightString(col1_x + col_width - 12, curr_y, val)

            c.setStrokeColor(colors.HexColor("#E2E8F0"))
            c.setLineWidth(0.5)
            c.line(col1_x + 12, curr_y - 4, col1_x + col_width - 12, curr_y - 4)
            curr_y -= 22

        curr_y -= 10
        # 4C Highlight Box
        c.setFillColor(colors.HexColor("#F1F5F9"))
        c.setStrokeColor(cls.GOLD)
        c.setLineWidth(1)
        c.roundRect(col1_x + 10, curr_y - 125, col_width - 20, 120, 4, fill=True, stroke=True)

        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(cls.GOLD)
        c.drawString(col1_x + 20, curr_y - 15, "GEMOLOGICAL SUMMARY (4Cs)")

        summary_items = [
            ("CARAT WEIGHT", f"{diamond_spec.get('carat', 1.0):.2f} ct"),
            ("COLOR GRADE", str(diamond_spec.get('color', 'F'))),
            ("CLARITY GRADE", str(diamond_spec.get('clarity', 'VS1'))),
            ("CUT GRADE", str(diamond_spec.get('cut', 'Ideal'))),
        ]
        sy = curr_y - 35
        for s_label, s_val in summary_items:
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(cls.NAVY)
            c.drawString(col1_x + 20, sy, s_label)

            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(cls.TEXT_DARK)
            c.drawRightString(col1_x + col_width - 20, sy, s_val)
            sy -= 20

        # -------------------------------------------------------------
        # PANEL 2: ADDITIONAL GRADING & PROPORTIONS
        # -------------------------------------------------------------
        cls._render_panel_header(c, col2_x, col_y + col_height - 28, col_width, "2. PROPORTIONS & FINISH")

        curr_y2 = col_y + col_height - 48

        specs_col2 = [
            ("Polish", str(diamond_spec.get("polish", "Excellent"))),
            ("Symmetry", str(diamond_spec.get("symmetry", "Excellent"))),
            ("Fluorescence", str(diamond_spec.get("fluorescence", "None"))),
            ("Measurements", diamond_spec.get("measurements_str", f"{diamond_spec.get('x', 6.46)} - {diamond_spec.get('y', 6.49)} x {diamond_spec.get('z', 4.00)} mm")),
            ("Table Size", f"{diamond_spec.get('table', 57.0)}%"),
            ("Total Depth", f"{diamond_spec.get('depth', 61.8)}%"),
            ("Girdle", str(diamond_spec.get("girdle", "Medium (Faceted)"))),
            ("Culet", str(diamond_spec.get("culet", "Pointed"))),
            ("Laser Inscription", str(diamond_spec.get("inscription", f"IGI {rep_no}"))),
        ]

        for label, val in specs_col2:
            c.setFont("Helvetica", 8.5)
            c.setFillColor(cls.TEXT_MUTED)
            c.drawString(col2_x + 12, curr_y2, label)

            c.setFont("Helvetica-Bold", 8.5)
            c.setFillColor(cls.TEXT_DARK)
            c.drawRightString(col2_x + col_width - 12, curr_y2, str(val)[:24])

            c.setStrokeColor(colors.HexColor("#E2E8F0"))
            c.setLineWidth(0.5)
            c.line(col2_x + 12, curr_y2 - 3, col2_x + col_width - 12, curr_y2 - 3)
            curr_y2 -= 18

        # Comments Section
        curr_y2 -= 5
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(cls.NAVY)
        c.drawString(col2_x + 12, curr_y2, "Comments / Growth Description:")
        curr_y2 -= 12
        comments_text = diamond_spec.get("comments", f"Official IGI report check for #{rep_no}. Certified grade.")
        c.setFont("Helvetica", 8)
        c.setFillColor(cls.TEXT_DARK)
        # Wrap comments text line
        c.drawString(col2_x + 12, curr_y2, comments_text[:45])
        if len(comments_text) > 45:
            c.drawString(col2_x + 12, curr_y2 - 10, comments_text[45:90])

        # Proportions Diagram Graphic
        cls._draw_proportions_diagram(c, col2_x + 40, col_y + 20, diamond_spec)

        # -------------------------------------------------------------
        # PANEL 3: SECURITY, SCALES & VERIFICATION QR
        # -------------------------------------------------------------
        cls._render_panel_header(c, col3_x, col_y + col_height - 28, col_width, "3. SECURITY & SCALES")

        curr_y3 = col_y + col_height - 48

        # Security Seal / Watermark Graphic
        c.setFillColor(colors.HexColor("#EFF6FF"))
        c.setStrokeColor(cls.NAVY)
        c.setLineWidth(1)
        c.roundRect(col3_x + 12, curr_y3 - 55, col_width - 24, 52, 4, fill=True, stroke=True)

        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(cls.NAVY)
        c.drawString(col3_x + 20, curr_y3 - 16, "IGI SECURITY REGISTRY")
        c.setFont("Helvetica", 8)
        c.setFillColor(cls.TEXT_MUTED)
        c.drawString(col3_x + 20, curr_y3 - 30, f"Verification Code: IGI-VAL-{rep_no[-6:]}")
        c.drawString(col3_x + 20, curr_y3 - 42, "Authenticity Micro-Print & Tamper Seal")

        # Color & Clarity Grading Scales Reference
        curr_y3 -= 70
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(cls.NAVY)
        c.drawString(col3_x + 12, curr_y3, "IGI CLARITY SCALE")
        curr_y3 -= 14
        
        clarity_tiers = ["FL/IF", "VVS1", "VVS2", "VS1", "VS2", "SI1", "SI2", "I1"]
        cell_w = (col_width - 24) / len(clarity_tiers)
        active_clarity = str(diamond_spec.get("clarity", "VS1")).upper()

        for idx, ct in enumerate(clarity_tiers):
            cx = col3_x + 12 + idx * cell_w
            is_active = (ct == active_clarity or (ct in active_clarity and len(ct) > 2))
            c.setFillColor(cls.GOLD if is_active else colors.HexColor("#F8FAFC"))
            c.setStrokeColor(cls.NAVY if is_active else cls.BORDER_COLOR)
            c.setLineWidth(1 if is_active else 0.5)
            c.rect(cx, curr_y3 - 14, cell_w, 16, fill=True, stroke=True)
            c.setFillColor(colors.white if is_active else cls.TEXT_DARK)
            c.setFont("Helvetica-Bold" if is_active else "Helvetica", 6.5)
            c.drawCentredString(cx + cell_w/2, curr_y3 - 10, ct)

        curr_y3 -= 28
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(cls.NAVY)
        c.drawString(col3_x + 12, curr_y3, "IGI COLOR SCALE")
        curr_y3 -= 14

        color_tiers = ["D", "E", "F", "G", "H", "I", "J", "K-Z"]
        cell_w_col = (col_width - 24) / len(color_tiers)
        active_color = str(diamond_spec.get("color", "F")).upper()

        for idx, cot in enumerate(color_tiers):
            cx = col3_x + 12 + idx * cell_w_col
            is_active = (cot == active_color or (cot in active_color and len(active_color) == 1))
            c.setFillColor(cls.GOLD if is_active else colors.HexColor("#F8FAFC"))
            c.setStrokeColor(cls.NAVY if is_active else cls.BORDER_COLOR)
            c.setLineWidth(1 if is_active else 0.5)
            c.rect(cx, curr_y3 - 14, cell_w_col, 16, fill=True, stroke=True)
            c.setFillColor(colors.white if is_active else cls.TEXT_DARK)
            c.setFont("Helvetica-Bold" if is_active else "Helvetica", 7)
            c.drawCentredString(cx + cell_w_col/2, curr_y3 - 10, cot)

        # QR Code Generation
        curr_y3 -= 35
        qr_value = f"https://lookup.igi.org/index.php/reports/verify/{rep_no}"
        try:
            qr_widget = qr.QrCodeWidget(qr_value)
            qr_bounds = qr_widget.getBounds()
            qr_w = qr_bounds[2] - qr_bounds[0]
            qr_h = qr_bounds[3] - qr_bounds[1]
            d = Drawing(70, 70, transform=[70/qr_w, 0, 0, 70/qr_h, 0, 0])
            d.add(qr_widget)
            d.drawOn(c, col3_x + (col_width - 70)/2, curr_y3 - 75)
        except Exception:
            # Fallback graphic if QR fails
            c.setFillColor(colors.HexColor("#E2E8F0"))
            c.rect(col3_x + (col_width - 60)/2, curr_y3 - 75, 60, 60, fill=True, stroke=True)

        curr_y3 -= 85
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(cls.NAVY)
        c.drawCentredString(col3_x + col_width/2, curr_y3, "SCAN TO VERIFY ON IGI.ORG")

        # Official Signature & Copyright Footer inside Panel 3
        c.setFont("Helvetica", 7)
        c.setFillColor(cls.TEXT_MUTED)
        c.drawCentredString(col3_x + col_width/2, col_y + 15, "International Gemological Institute © 2026")
        c.drawCentredString(col3_x + col_width/2, col_y + 6, "All rights reserved. Terms & Conditions apply.")

        # Save and return PDF bytes
        c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @classmethod
    def _render_panel_header(cls, c, x, y, width, title):
        c.setFillColor(cls.NAVY)
        c.roundRect(x + 4, y, width - 8, 22, 4, fill=True, stroke=False)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.white)
        c.drawCentredString(x + width/2, y + 6, title)

    @classmethod
    def _draw_proportions_diagram(cls, c, x, y, diamond_spec):
        """Draws a clean proportion diagram of a round brilliant diamond."""
        table_pct = float(diamond_spec.get("table", 57.0))
        depth_pct = float(diamond_spec.get("depth", 61.8))

        c.setStrokeColor(cls.NAVY)
        c.setLineWidth(1)
        c.setFillColor(colors.HexColor("#F8FAFC"))

        # Diamond Crown & Pavilion Polygon coordinates
        # Table top
        t_half = 30 * (table_pct / 60.0)
        top_y = y + 70
        girdle_y = y + 45
        culet_y = y + 10
        center_x = x + 70

        # Draw Table line
        c.line(center_x - t_half, top_y, center_x + t_half, top_y)
        # Crown facets
        c.line(center_x - t_half, top_y, center_x - 50, girdle_y)
        c.line(center_x + t_half, top_y, center_x + 50, girdle_y)
        # Girdle line
        c.line(center_x - 50, girdle_y, center_x + 50, girdle_y)
        c.line(center_x - 50, girdle_y - 3, center_x + 50, girdle_y - 3)
        # Pavilion facets
        c.line(center_x - 50, girdle_y - 3, center_x, culet_y)
        c.line(center_x + 50, girdle_y - 3, center_x, culet_y)

        # Dimension labels
        c.setFont("Helvetica", 7.5)
        c.setFillColor(cls.NAVY)
        c.drawCentredString(center_x, top_y + 4, f"Table: {table_pct}%")
        c.drawString(center_x + 55, (top_y + culet_y)/2, f"Depth: {depth_pct}%")
