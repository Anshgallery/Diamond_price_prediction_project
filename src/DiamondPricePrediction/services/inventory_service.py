import os
import json
import sqlite3
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from DiamondPricePrediction.utils.logger import logging
from DiamondPricePrediction.services.indian_market_service import IndianMarketService

class InventoryService:
    """
    Jeweller Workspace, Inventory Portfolio, Watchlist & Appraisal Storage.
    Uses SQLite database with user-isolated records and Indian Rupee (₹) metrics.
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
        """Initialize database tables for inventory, appraisals, and watchlist with schema validation."""
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if inventory table has jeweller_id; if not, recreate or add
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
                table_exists = cursor.fetchone()
                if table_exists:
                    cursor.execute("PRAGMA table_info(inventory)")
                    columns = [row[1] for row in cursor.fetchall()]
                    if "jeweller_id" not in columns:
                        cursor.execute("DROP TABLE IF EXISTS inventory")
                        cursor.execute("DROP TABLE IF EXISTS valuation_logs")

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS inventory (
                        id TEXT PRIMARY KEY,
                        jeweller_id TEXT DEFAULT 'default',
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
                        buying_price_inr REAL,
                        fair_market_inr REAL,
                        suggested_sell_inr REAL,
                        profit_inr REAL,
                        margin_pct REAL,
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
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS valuation_logs (
                        id TEXT PRIMARY KEY,
                        jeweller_id TEXT DEFAULT 'default',
                        report_number TEXT,
                        origin_type TEXT,
                        carat REAL,
                        cut TEXT,
                        color TEXT,
                        clarity TEXT,
                        buying_price_inr REAL,
                        fair_market_inr REAL,
                        suggested_sell_inr REAL,
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
        buying_price_inr: Optional[float] = None,
        status: str = "In Stock",
        tag: str = "Inventory",
        client_name: str = "",
        notes: str = "",
        jeweller_id: str = "default"
    ) -> str:
        """Save an appraised IGI diamond to jeweller workspace."""
        cls.init_db()
        item_id = str(uuid.uuid4())[:8].upper()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        stock_num = f"IGI-{item_id}"
        report_num = str(diamond_spec.get("report_number") or "N/A")

        fair_market = float(valuation_result.get("fair_market_value") or 0)
        suggested_buy = float(valuation_result.get("suggested_buy_price") or 0)
        suggested_sell = float(valuation_result.get("suggested_sell_price") or 0)
        
        actual_buy = float(buying_price_inr) if buying_price_inr and buying_price_inr > 0 else suggested_buy
        profit = round(suggested_sell - actual_buy)
        margin = round((profit / max(suggested_sell, 1.0)) * 100.0, 1)

        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inventory (
                    id, jeweller_id, stock_number, report_number, origin_type, shape,
                    carat, cut, color, clarity, polish, symmetry, fluorescence,
                    depth, table_pct, x, y, z, buying_price_inr,
                    fair_market_inr, suggested_sell_inr, profit_inr, margin_pct,
                    confidence_score, status, tag, client_name, notes,
                    dossier_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                jeweller_id,
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
                float(diamond_spec.get("depth", 61.8)),
                float(diamond_spec.get("table", 57.0)),
                float(diamond_spec.get("x", 0)),
                float(diamond_spec.get("y", 0)),
                float(diamond_spec.get("z", 0)),
                actual_buy,
                fair_market,
                suggested_sell,
                profit,
                margin,
                int(valuation_result.get("confidence_score") or 0),
                status,
                tag,
                client_name,
                notes,
                json.dumps({
                    "diamond_spec": diamond_spec,
                    "valuation": valuation_result,
                    "buying_price_inr": actual_buy
                }),
                now,
                now
            ))

            # Log to valuation audit history
            cursor.execute("""
                INSERT INTO valuation_logs (
                    id, jeweller_id, report_number, origin_type, carat, cut, color, clarity,
                    buying_price_inr, fair_market_inr, suggested_sell_inr, deal_rating, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4())[:8],
                jeweller_id,
                report_num,
                diamond_spec.get("origin_type", "Natural"),
                float(diamond_spec.get("carat", 0)),
                diamond_spec.get("cut", "Ideal"),
                diamond_spec.get("color", "E"),
                diamond_spec.get("clarity", "VS1"),
                actual_buy,
                fair_market,
                suggested_sell,
                valuation_result.get("jeweller_deal", {}).get("deal_rating", "Appraised") if valuation_result.get("jeweller_deal") else "Appraised",
                now
            ))
            conn.commit()

        logging.info(f"Saved diamond item #{item_id} to jeweller inventory.")
        return item_id

    @classmethod
    def get_inventory(
        cls,
        status_filter: Optional[str] = None,
        tag_filter: Optional[str] = None,
        query: Optional[str] = None,
        jeweller_id: str = "default"
    ) -> List[Dict[str, Any]]:
        """Retrieve jeweller inventory with formatted Indian Rupee values."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM inventory WHERE (jeweller_id = ? OR jeweller_id = 'default')"
            params = [jeweller_id]

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
            
            results = []
            for r in rows:
                item = dict(r)
                item["fair_market_formatted"] = IndianMarketService.format_inr(item.get("fair_market_inr"))
                item["suggested_sell_formatted"] = IndianMarketService.format_inr(item.get("suggested_sell_inr"))
                item["buying_price_formatted"] = IndianMarketService.format_inr(item.get("buying_price_inr"))
                item["profit_formatted"] = IndianMarketService.format_inr(item.get("profit_inr"))
                results.append(item)
            return results

    @classmethod
    def get_diamond_by_id(cls, item_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single inventory item by ID."""
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
                d["fair_market_formatted"] = IndianMarketService.format_inr(d.get("fair_market_inr"))
                d["suggested_sell_formatted"] = IndianMarketService.format_inr(d.get("suggested_sell_inr"))
                d["buying_price_formatted"] = IndianMarketService.format_inr(d.get("buying_price_inr"))
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
    def get_summary_stats(cls, jeweller_id: str = "default") -> Dict[str, Any]:
        """Calculate workspace portfolio metrics in Indian ₹."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*), SUM(fair_market_inr), SUM(buying_price_inr), SUM(profit_inr), AVG(confidence_score)
                FROM inventory WHERE (jeweller_id = ? OR jeweller_id = 'default')
            """, (jeweller_id,))
            total_count, total_market, total_cost, total_profit, avg_conf = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) FROM valuation_logs WHERE (jeweller_id = ? OR jeweller_id = 'default')", (jeweller_id,))
            total_appraisals = cursor.fetchone()[0]

            tot_market = total_market or 0
            tot_cost = total_cost or 0
            tot_profit = total_profit or 0

            return {
                "inventory_count": total_count or 0,
                "total_portfolio_market_inr": tot_market,
                "total_portfolio_market_formatted": IndianMarketService.format_inr(tot_market),
                "total_portfolio_market_lakhs": IndianMarketService.format_inr_lakhs(tot_market),
                "total_acquisition_cost_inr": tot_cost,
                "total_acquisition_cost_formatted": IndianMarketService.format_inr(tot_cost),
                "total_expected_profit_inr": tot_profit,
                "total_expected_profit_formatted": IndianMarketService.format_inr(tot_profit),
                "avg_confidence": round(avg_conf or 0, 1),
                "total_appraisals_logged": total_appraisals or 0
            }
