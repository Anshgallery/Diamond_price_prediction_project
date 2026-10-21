import os
import sqlite3
import uuid
from typing import Dict, Any, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from DiamondPricePrediction.utils.logger import logging

class AuthService:
    """
    Secure Jeweller Authentication Service.
    Handles jeweller account creation, password hashing, verification,
    and profile management.
    """

    DB_PATH = os.path.join("artifacts", "jeweller_workspace.db")

    @classmethod
    def _get_connection(cls) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_users_table(cls):
        """Create users table and default jeweller profile if empty."""
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS jewellers (
                        id TEXT PRIMARY KEY,
                        business_name TEXT NOT NULL,
                        owner_name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        city TEXT DEFAULT 'Mumbai',
                        gst_number TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                # Migrate optional columns
                for col in ["address", "phone"]:
                    try:
                        cursor.execute(f"ALTER TABLE jewellers ADD COLUMN {col} TEXT")
                    except sqlite3.OperationalError:
                        pass
                conn.commit()

                # Seed default profile if table is empty
                cursor.execute("SELECT COUNT(*) FROM jewellers")
                count = cursor.fetchone()[0]
                if count == 0:
                    demo_id = "default"
                    demo_hash = generate_password_hash("jeweller123")
                    cursor.execute("""
                        INSERT INTO jewellers (id, business_name, owner_name, email, password_hash, city, gst_number, address, phone)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (demo_id, "GemForecast Fine Jewels", "Master Jeweller", "jeweller@gemforecast.com", demo_hash, "Mumbai", "27AABCG1234F1Z5", "Bullion Plaza, Zaveri Bazaar, Mumbai 400002", "+91 98200 11223"))
                    conn.commit()
                    logging.info("Default jeweller profile created: jeweller@gemforecast.com")
        except Exception as e:
            logging.error(f"Error initializing jeweller auth table: {e}")

    @classmethod
    def register_jeweller(
        cls,
        business_name: str,
        owner_name: str,
        email: str,
        password: str,
        city: str = "Mumbai",
        gst_number: str = "",
        address: str = "",
        phone: str = ""
    ) -> Dict[str, Any]:
        """Register a new jeweller with secure hashed credentials."""
        cls.init_users_table()
        email_clean = email.strip().lower()

        if not email_clean or not password or len(password) < 6:
            return {"success": False, "error": "Password must be at least 6 characters."}

        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM jewellers WHERE email = ?", (email_clean,))
                if cursor.fetchone():
                    return {"success": False, "error": "An account with this email already exists."}

                new_id = str(uuid.uuid4())[:8]
                pwd_hash = generate_password_hash(password)

                cursor.execute("""
                    INSERT INTO jewellers (id, business_name, owner_name, email, password_hash, city, gst_number, address, phone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (new_id, business_name.strip(), owner_name.strip(), email_clean, pwd_hash, city.strip(), gst_number.strip(), address.strip(), phone.strip()))
                conn.commit()

                logging.info(f"Registered new jeweller: {business_name} ({email_clean})")
                return {
                    "success": True,
                    "jeweller": {
                        "id": new_id,
                        "business_name": business_name,
                        "owner_name": owner_name,
                        "email": email_clean,
                        "city": city,
                        "gst_number": gst_number,
                        "address": address,
                        "phone": phone
                    }
                }
        except Exception as e:
            logging.error(f"Registration failed: {e}")
            return {"success": False, "error": f"Registration failed: {str(e)}"}

    @classmethod
    def authenticate(cls, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify jeweller login credentials."""
        cls.init_users_table()
        email_clean = email.strip().lower()

        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM jewellers WHERE email = ?", (email_clean,))
                row = cursor.fetchone()
                if row and check_password_hash(row["password_hash"], password):
                    return {
                        "id": row["id"],
                        "business_name": row["business_name"],
                        "owner_name": row["owner_name"],
                        "email": row["email"],
                        "city": row["city"],
                        "gst_number": row["gst_number"],
                        "address": row["address"] if "address" in row.keys() else "",
                        "phone": row["phone"] if "phone" in row.keys() else ""
                    }
                return None
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return None

    @classmethod
    def get_jeweller_by_id(cls, jeweller_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Retrieves jeweller profile by ID or gets default."""
        cls.init_users_table()
        try:
            with cls._get_connection() as conn:
                cursor = conn.cursor()
                if jeweller_id and jeweller_id not in ("default", "admin"):
                    cursor.execute("SELECT * FROM jewellers WHERE id = ?", (jeweller_id,))
                    row = cursor.fetchone()
                    if row:
                        return {
                            "id": row["id"],
                            "business_name": row["business_name"],
                            "owner_name": row["owner_name"],
                            "email": row["email"],
                            "city": row["city"],
                            "gst_number": row["gst_number"] or "",
                            "address": row["address"] if "address" in row.keys() and row["address"] else f"{row['city']}, India",
                            "phone": row["phone"] if "phone" in row.keys() and row["phone"] else ""
                        }

                # Fallback to first jeweller in DB or default
                cursor.execute("SELECT * FROM jewellers ORDER BY created_at ASC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row["id"],
                        "business_name": row["business_name"],
                        "owner_name": row["owner_name"],
                        "email": row["email"],
                        "city": row["city"],
                        "gst_number": row["gst_number"] or "",
                        "address": row["address"] if "address" in row.keys() and row["address"] else f"{row['city']}, India",
                        "phone": row["phone"] if "phone" in row.keys() and row["phone"] else ""
                    }
        except Exception as e:
            logging.error(f"Error fetching jeweller {jeweller_id}: {e}")
        return {
            "id": "default",
            "business_name": "GemForecast Fine Jewels",
            "owner_name": "Master Jeweller",
            "email": "billing@gemforecast.com",
            "city": "Mumbai",
            "gst_number": "27AABCG1234F1Z5",
            "address": "Bullion Plaza, Zaveri Bazaar, Mumbai 400002",
            "phone": "+91 98200 11223"
        }

