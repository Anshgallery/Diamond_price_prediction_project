import os
import json
import sqlite3
import uuid
import secrets
from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from DiamondPricePrediction.utils.logger import logging
from DiamondPricePrediction.services.jewellery_calculator import JewelleryCalculator
from DiamondPricePrediction.services.einvoice_service import EInvoiceService

class InvoiceService:
    """
    Secure Jeweller Invoice & Bill History Management Service.
    
    Features:
      - Persistent relational storage in SQLite (with schema migrations).
      - Sequential, GST-compliant invoice numbering (e.g. GF-2026-0001).
      - Unique, cryptographically secure customer share links.
      - Full customer KYC details (Name, Phone, Address, GSTIN, PAN).
      - Official Indian e-Invoice metadata: IRN, Ack No, Ack Date, e-Invoice QR code.
      - Strict privacy separation: Customer view conceals jeweller landed costs & margins.
    """

    DB_PATH = os.environ.get("DATABASE_PATH", os.path.join("artifacts", "jeweller_workspace.db"))

    @classmethod
    def _get_connection(cls) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Initializes invoices table and indexes with optional dispatch columns."""
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS invoices (
                        id TEXT PRIMARY KEY,
                        invoice_number TEXT UNIQUE NOT NULL,
                        share_token TEXT UNIQUE NOT NULL,
                        jeweller_id TEXT DEFAULT 'default',
                        customer_name TEXT NOT NULL,
                        customer_phone TEXT,
                        customer_email TEXT,
                        customer_address TEXT,
                        customer_gstin TEXT,
                        customer_pan TEXT,
                        invoice_date TEXT NOT NULL,
                        due_date TEXT,
                        status TEXT DEFAULT 'Issued',
                        item_description TEXT,
                        calculation_json TEXT NOT NULL,
                        landed_cost REAL NOT NULL,
                        taxable_amount REAL NOT NULL,
                        total_gst REAL NOT NULL,
                        grand_total REAL NOT NULL,
                        profit_amount REAL NOT NULL,
                        margin_pct REAL NOT NULL,
                        notes TEXT,
                        delivery_note TEXT,
                        payment_terms TEXT,
                        buyer_order_no TEXT,
                        dispatched_through TEXT,
                        destination TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_jeweller ON invoices(jeweller_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_share ON invoices(share_token)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(created_at)")

                # Try adding dispatch columns if table already existed without them
                for col in ["delivery_note", "payment_terms", "buyer_order_no", "dispatched_through", "destination"]:
                    try:
                        cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col} TEXT")
                    except sqlite3.OperationalError:
                        pass

                conn.commit()
            logging.info("Invoice service database initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing invoice database: {e}")

    @classmethod
    def _generate_next_invoice_number(cls, conn: sqlite3.Connection) -> str:
        """Generates sequential invoice number e.g. GF-2026-0001."""
        year_str = datetime.now(timezone.utc).strftime("%Y")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE invoice_number LIKE ?", (f"GF-{year_str}-%",))
        count = cursor.fetchone()[0]
        return f"GF-{year_str}-{count + 1:04d}"

    @classmethod
    def create_invoice(cls, form_data: Dict[str, Any], jeweller_id: str = "default") -> Dict[str, Any]:
        """Creates and stores a verified, GST-compliant invoice."""
        cls.init_db()

        # Run calculation through Decimal engine
        calc_res = JewelleryCalculator.calculate(form_data)

        ist_tz = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist_tz)
        invoice_date_str = form_data.get("invoice_date") or now_ist.strftime("%d %b %Y")
        due_date_str = form_data.get("due_date") or (now_ist + timedelta(days=15)).strftime("%d %b %Y")

        inv_id = uuid.uuid4().hex
        share_token = secrets.token_urlsafe(18)

        customer_name = str(form_data.get("customer_name", "Valued Customer")).strip()
        customer_phone = str(form_data.get("customer_phone", "")).strip()
        customer_email = str(form_data.get("customer_email", "")).strip()
        customer_address = str(form_data.get("customer_address", "")).strip()
        customer_gstin = str(form_data.get("customer_gstin", "")).strip().upper()
        customer_pan = str(form_data.get("customer_pan", "")).strip().upper()
        notes = str(form_data.get("notes", "Thank you for your business. Certified authentic BIS hallmarked jewellery.")).strip()

        delivery_note = str(form_data.get("delivery_note", "")).strip()
        payment_terms = str(form_data.get("payment_terms", "Immediate / RTGS / Card / Cash")).strip()
        buyer_order_no = str(form_data.get("buyer_order_no", "")).strip()
        dispatched_through = str(form_data.get("dispatched_through", "Hand Delivery (Store Counter)")).strip()
        destination = str(form_data.get("destination", customer_address or "Store Counter")).strip()

        # Item description headline
        metal_desc = calc_res.get("metal_label", "Fine Jewellery")
        dia_desc = calc_res.get("diamond_label", "")
        item_headline = f"{metal_desc} • {dia_desc}" if calc_res.get("enable_diamond") else metal_desc

        try:
            with cls._get_connection() as conn:
                invoice_number = cls._generate_next_invoice_number(conn)
                now_iso = datetime.now(timezone.utc).isoformat()

                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO invoices (
                        id, invoice_number, share_token, jeweller_id,
                        customer_name, customer_phone, customer_email, customer_address,
                        customer_gstin, customer_pan, invoice_date, due_date, status,
                        item_description, calculation_json, landed_cost, taxable_amount,
                        total_gst, grand_total, profit_amount, margin_pct, notes,
                        delivery_note, payment_terms, buyer_order_no, dispatched_through, destination,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inv_id, invoice_number, share_token, jeweller_id,
                    customer_name, customer_phone, customer_email, customer_address,
                    customer_gstin, customer_pan, invoice_date_str, due_date_str, "Issued",
                    item_headline, json.dumps(calc_res),
                    calc_res["landed_cost"], calc_res["taxable_amount"],
                    calc_res["total_gst"], calc_res["grand_total"],
                    calc_res["profit_amount"], calc_res["margin_pct"], notes,
                    delivery_note, payment_terms, buyer_order_no, dispatched_through, destination,
                    now_iso, now_iso
                ))
                conn.commit()

            logging.info(f"Created invoice #{invoice_number} ({inv_id}) for {customer_name}.")
            return {
                "success": True,
                "invoice_id": inv_id,
                "invoice_number": invoice_number,
                "share_token": share_token,
                "grand_total": calc_res["grand_total"],
                "formatted_grand_total": calc_res["formatted_grand_total"]
            }
        except Exception as e:
            logging.error(f"Error creating invoice: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def get_invoice_by_id(cls, invoice_id: str, jeweller_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves invoice by ID."""
        cls.init_db()
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                if jeweller_id and jeweller_id != "admin":
                    cursor.execute("SELECT * FROM invoices WHERE id = ? AND jeweller_id = ?", (invoice_id, jeweller_id))
                else:
                    cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
                row = cursor.fetchone()
                if row:
                    return cls._row_to_dict(row)
        except Exception as e:
            logging.error(f"Error getting invoice {invoice_id}: {e}")
        return None

    @classmethod
    def get_invoice_by_share_token(cls, share_token: str) -> Optional[Dict[str, Any]]:
        """Retrieves invoice by public share token."""
        cls.init_db()
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM invoices WHERE share_token = ?", (share_token.strip(),))
                row = cursor.fetchone()
                if row:
                    return cls._row_to_dict(row)
        except Exception as e:
            logging.error(f"Error retrieving invoice by share token: {e}")
        return None

    @classmethod
    def list_invoices(
        cls,
        jeweller_id: str = "default",
        query: str = "",
        status_filter: str = "All",
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves bill history with optional query, status filters, and limit."""
        cls.init_db()
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                sql = "SELECT * FROM invoices WHERE (jeweller_id = ? OR jeweller_id = 'default')"
                params: List[Any] = [jeweller_id]

                if status_filter and status_filter != "All":
                    sql += " AND status = ?"
                    params.append(status_filter)

                if query and query.strip():
                    sql += " AND (customer_name LIKE ? OR invoice_number LIKE ? OR customer_phone LIKE ?)"
                    q = f"%{query.strip()}%"
                    params.extend([q, q, q])

                sql += " ORDER BY created_at DESC"
                if limit and isinstance(limit, int) and limit > 0:
                    sql += " LIMIT ?"
                    params.append(limit)

                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()
                return [cls._row_to_dict(r) for r in rows]
        except Exception as e:
            logging.error(f"Error listing invoices: {e}")
            return []

    @classmethod
    def update_status(cls, invoice_id: str, new_status: str, jeweller_id: str = "default") -> bool:
        """Updates payment/delivery status."""
        cls.init_db()
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                now_iso = datetime.now(timezone.utc).isoformat()
                cursor.execute(
                    "UPDATE invoices SET status = ?, updated_at = ? WHERE id = ?",
                    (new_status, now_iso, invoice_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating invoice status: {e}")
            return False

    @classmethod
    def delete_invoice(cls, invoice_id: str, jeweller_id: str = "default") -> bool:
        """Deletes an invoice."""
        cls.init_db()
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting invoice: {e}")
            return False

    @classmethod
    def get_invoice_stats(cls, jeweller_id: str = "default") -> Dict[str, Any]:
        """Computes summary statistics across saved bills."""
        cls.init_db()
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(*),
                        COALESCE(SUM(grand_total), 0),
                        COALESCE(SUM(taxable_amount), 0),
                        COALESCE(SUM(total_gst), 0),
                        COALESCE(SUM(profit_amount), 0)
                    FROM invoices 
                    WHERE (jeweller_id = ? OR jeweller_id = 'default')
                """, (jeweller_id,))
                row = cursor.fetchone()
                count, grand_total, taxable, total_gst, profit = row

                return {
                    "total_invoices": count,
                    "total_revenue": grand_total,
                    "total_taxable": taxable,
                    "total_gst": total_gst,
                    "total_profit": profit,
                    "formatted_revenue": JewelleryCalculator.format_inr(grand_total),
                    "formatted_gst": JewelleryCalculator.format_inr(total_gst),
                    "formatted_profit": JewelleryCalculator.format_inr(profit)
                }
        except Exception as e:
            logging.error(f"Error computing invoice stats: {e}")
            return {
                "total_invoices": 0, "total_revenue": 0, "total_taxable": 0,
                "total_gst": 0, "total_profit": 0, "formatted_revenue": "₹ 0",
                "formatted_gst": "₹ 0", "formatted_profit": "₹ 0"
            }

    @classmethod
    def _row_to_dict(cls, row: sqlite3.Row) -> Dict[str, Any]:
        """Converts sqlite Row to rich dictionary with full e-Invoice package."""
        d = dict(row)
        try:
            d["calc"] = json.loads(d["calculation_json"])
        except Exception:
            d["calc"] = {}

        # Fallback or ensure line_items and hsn_summary exist in calc
        if "line_items" not in d["calc"] or not d["calc"]["line_items"]:
            recalc = JewelleryCalculator.calculate(d["calc"])
            d["calc"]["line_items"] = recalc.get("line_items", [])
            d["calc"]["hsn_summary"] = recalc.get("hsn_summary", [])
            d["calc"]["amount_chargeable_words"] = recalc.get("amount_chargeable_words", JewelleryCalculator.number_to_indian_words(int(d["grand_total"]), "Indian Rupee "))
            d["calc"]["tax_amount_words"] = recalc.get("tax_amount_words", JewelleryCalculator.number_to_indian_words(int(d["total_gst"]), "Indian Rupee "))

        d["formatted_grand_total"] = JewelleryCalculator.format_inr(d["grand_total"])
        d["formatted_taxable"] = JewelleryCalculator.format_inr(d["taxable_amount"])
        d["formatted_gst"] = JewelleryCalculator.format_inr(d["total_gst"])
        d["formatted_profit"] = JewelleryCalculator.format_inr(d["profit_amount"])
        d["formatted_landed"] = JewelleryCalculator.format_inr(d["landed_cost"])

        # Default Jeweller Profile
        seller_gstin = "27AABCS1429B1Z8"
        buyer_gstin = d.get("customer_gstin") or ""

        # Build official e-Invoice package (IRN, Ack No, Ack Date, QR SVG)
        einvoice = EInvoiceService.get_full_einvoice_package(
            supplier_gstin=seller_gstin,
            buyer_gstin=buyer_gstin,
            doc_no=d["invoice_number"],
            doc_date_str=d["invoice_date"],
            grand_total=d["grand_total"],
            item_count=len(d["calc"].get("line_items", [])) or 1,
            main_hsn="7113"
        )
        d["einvoice"] = einvoice

        # Build standard Tally e-Invoice Dispatch Metadata
        inv_date_formatted = EInvoiceService.format_ack_date(d["invoice_date"])
        d["dispatch"] = {
            "invoice_no": d["invoice_number"],
            "dated": inv_date_formatted,
            "delivery_note": d.get("delivery_note") or "",
            "mode_terms_of_payment": d.get("payment_terms") or "Immediate / RTGS / Card / Cash",
            "reference_no_date": "",
            "other_references": "",
            "buyer_order_no": d.get("buyer_order_no") or "",
            "order_dated": inv_date_formatted if d.get("buyer_order_no") else "",
            "dispatch_doc_no": "",
            "delivery_note_date": "",
            "dispatched_through": d.get("dispatched_through") or "Hand Delivery (Store Counter)",
            "destination": d.get("destination") or d.get("customer_address") or "Store Counter, Mumbai",
            "terms_of_delivery": "Goods once sold are certified authentic BIS hallmarked items."
        }

        return d
