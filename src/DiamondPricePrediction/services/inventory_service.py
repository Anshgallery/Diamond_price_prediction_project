import os
import json
import sqlite3
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from DiamondPricePrediction.utils.logger import logging

class InventoryService:
    """
    Jeweller Inventory, Appraisal History & Workspace Storage Service.
    Uses SQLite database for local persistence of diamond dossiers, memo items,
    stock inventory, and audit logs.
    """

    DB_PATH = os.path.join("artifacts", "jeweller_workspace.db")

    @classmethod
    def _get_connection(cls) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Initialize database tables if they do not exist."""
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                # Diamonds Inventory Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS inventory (
                        id TEXT PRIMARY KEY,
                        stock_number TEXT,
                        report_number TEXT,
                        origin_type TEXT,
                        shape TEXT,
                        carat REAL,
                        cut TEXT,
                        color TEXT,
                        clarity TEXT,
                        polish TEXT,
                        symmetry TEXT,
                        fluorescence TEXT,
                        depth REAL,
                        table_pct REAL,
                        x REAL,
                        y REAL,
                        z REAL,
                        asking_price REAL,
                        valuation_midpoint REAL,
                        valuation_low REAL,
                        valuation_high REAL,
                        confidence_score INTEGER,
                        status TEXT DEFAULT 'In Stock',
                        tag TEXT DEFAULT 'General',
                        client_name TEXT,
                        notes TEXT,
                        dossier_json TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                """)
                # Valuation History Log Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS valuation_logs (
                        id TEXT PRIMARY KEY,
                        report_number TEXT,
                        carat REAL,
                        cut TEXT,
                        color TEXT,
                        clarity TEXT,
                        asking_price REAL,
                        valuation_midpoint REAL,
                        deal_rating TEXT,
                        created_at TEXT
                    )
                """)
                conn.commit()
            logging.info("Jeweller workspace database initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize inventory database: {e}")

    @classmethod
    def save_diamond(
        cls,
        diamond_spec: Dict[str, Any],
        valuation_result: Dict[str, Any],
        asking_price: Optional[float] = None,
        status: str = "In Stock",
        tag: str = "Inventory",
        client_name: str = "",
        notes: str = ""
    ) -> str:
        """Save an appraised diamond to inventory."""
        cls.init_db()
        item_id = str(uuid.uuid4())[:8].upper()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        stock_num = f"GEM-{item_id}"
        report_num = str(diamond_spec.get("report_number") or "N/A")

        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inventory (
                    id, stock_number, report_number, origin_type, shape,
                    carat, cut, color, clarity, polish, symmetry, fluorescence,
                    depth, table_pct, x, y, z, asking_price,
                    valuation_midpoint, valuation_low, valuation_high,
                    confidence_score, status, tag, client_name, notes,
                    dossier_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                stock_num,
                report_num,
                diamond_spec.get("origin_type", "Natural"),
                diamond_spec.get("shape", "Round Brilliant"),
                float(diamond_spec.get("carat", 0)),
                diamond_spec.get("cut", "Ideal"),
                diamond_spec.get("color", "E"),
                diamond_spec.get("clarity", "VS1"),
                diamond_spec.get("polish", "Excellent"),
                diamond_spec.get("symmetry", "Excellent"),
                diamond_spec.get("fluorescence", "None"),
                float(diamond_spec.get("depth", 61.7)),
                float(diamond_spec.get("table", 57.0)),
                float(diamond_spec.get("x", 0)),
                float(diamond_spec.get("y", 0)),
                float(diamond_spec.get("z", 0)),
                float(asking_price or 0),
                float(valuation_result.get("midpoint_value") or 0),
                float(valuation_result.get("low_estimate") or 0),
                float(valuation_result.get("high_estimate") or 0),
                int(valuation_result.get("confidence_score") or 0),
                status,
                tag,
                client_name,
                notes,
                json.dumps({
                    "diamond_spec": diamond_spec,
                    "valuation": valuation_result,
                    "asking_price": asking_price
                }),
                now,
                now
            ))

            # Also record in valuation logs
            cursor.execute("""
                INSERT INTO valuation_logs (
                    id, report_number, carat, cut, color, clarity,
                    asking_price, valuation_midpoint, deal_rating, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4())[:8],
                report_num,
                float(diamond_spec.get("carat", 0)),
                diamond_spec.get("cut", "Ideal"),
                diamond_spec.get("color", "E"),
                diamond_spec.get("clarity", "VS1"),
                float(asking_price or 0),
                float(valuation_result.get("midpoint_value") or 0),
                valuation_result.get("jeweller_deal", {}).get("deal_rating", "Appraised") if valuation_result.get("jeweller_deal") else "Appraised",
                now
            ))

            conn.commit()

        logging.info(f"Saved diamond item #{item_id} to inventory.")
        return item_id

    @classmethod
    def get_inventory(
        cls,
        status_filter: Optional[str] = None,
        tag_filter: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve inventory list with optional filters."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM inventory WHERE 1=1"
            params = []

            if status_filter and status_filter != "All":
                sql += " AND status = ?"
                params.append(status_filter)

            if tag_filter and tag_filter != "All":
                sql += " AND tag = ?"
                params.append(tag_filter)

            if query and query.strip():
                sql += " AND (stock_number LIKE ? OR report_number LIKE ? OR client_name LIKE ? OR shape LIKE ?)"
                q_wild = f"%{query.strip()}%"
                params.extend([q_wild, q_wild, q_wild, q_wild])

            sql += " ORDER BY created_at DESC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @classmethod
    def get_diamond_by_id(cls, item_id: str) -> Optional[Dict[str, Any]]:
        """Get single diamond record by ID."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventory WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                if d.get("dossier_json"):
                    try:
                        d["dossier"] = json.loads(d["dossier_json"])
                    except Exception:
                        d["dossier"] = None
                return d
            return None

    @classmethod
    def delete_diamond(cls, item_id: str) -> bool:
        """Delete an inventory item."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
            conn.commit()
            return cursor.rowcount > 0

    @classmethod
    def get_valuation_logs(cls, limit: int = 25) -> List[Dict[str, Any]]:
        """Retrieve recent valuation audit history."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM valuation_logs ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    @classmethod
    def get_summary_stats(cls) -> Dict[str, Any]:
        """Compute workspace dashboard metrics."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(valuation_midpoint), SUM(asking_price), AVG(confidence_score) FROM inventory")
            total_count, total_value, total_asking, avg_conf = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) FROM valuation_logs")
            total_appraisals = cursor.fetchone()[0]

            return {
                "inventory_count": total_count or 0,
                "total_portfolio_value": round(total_value or 0, 2),
                "total_acquisition_cost": round(total_asking or 0, 2),
                "avg_confidence": round(avg_conf or 0, 1),
                "total_appraisals_logged": total_appraisals or 0
            }
