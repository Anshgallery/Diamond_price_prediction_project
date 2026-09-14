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

                # Seed default demo jeweller if table is empty
                cursor.execute("SELECT COUNT(*) FROM jewellers")
                count = cursor.fetchone()[0]
                if count == 0:
                    demo_id = str(uuid.uuid4())[:8]
                    demo_hash = generate_password_hash("jeweller123")
                    cursor.execute("""
                        INSERT INTO jewellers (id, business_name, owner_name, email, password_hash, city, gst_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (demo_id, "Shree Ganesh Gems & Jewels", "Rajesh Zaveri", "jeweller@zaveribazaar.in", demo_hash, "Mumbai (Zaveri Bazaar)", "27AABCS1429B1Z8"))
                    conn.commit()
                    logging.info("Default jeweller profile created: jeweller@zaveribazaar.in")
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
        gst_number: str = ""
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
                    INSERT INTO jewellers (id, business_name, owner_name, email, password_hash, city, gst_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (new_id, business_name.strip(), owner_name.strip(), email_clean, pwd_hash, city.strip(), gst_number.strip()))
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
                        "gst_number": gst_number
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
                        "gst_number": row["gst_number"]
                    }
                return None
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return None
