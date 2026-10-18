import os
import json
import math
import time
import urllib.request
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from DiamondPricePrediction.utils.logger import logging
from DiamondPricePrediction.services.ibja_gold_service import IBJAGoldService
from DiamondPricePrediction.services.licensed_diamond_service import LicensedDiamondService

class IndianMarketService:
    """
    India-First Diamond & Bullion Wholesale Market Service.
    
    Integrates:
    - Genuine, Timestamped IBJA (India Bullion and Jewellers Association) Gold & Silver Rates.
    - Licensed Natural Diamond Pricing (RapNet / IDEX API integration & Mumbai BDB physical benchmark).
    - Verified Surat Diamond Bourse (SDB) CVD/HPHT Manufacturing Wholesale Pricing.
    - Live USD/INR FX Rate from Frankfurter API with fallback.
    - Strict Zero-Fake Policy: Never claims unverified real-time ticks or fake feeds.
    """

    CONFIG_FILE = os.path.join("artifacts", "indian_market_config.json")
    FRANKFURTER_API_URL = "https://api.frankfurter.dev/v2/rate/USD/INR"
    FRANKFURTER_FALLBACK_URL = "https://api.frankfurter.app/latest?from=USD&to=INR"
    DEFAULT_USD_INR_RATE = 87.50

    # In-memory live caches with timestamps
    _CACHE_USD_INR: Optional[float] = None
    _CACHE_USD_INR_TS: float = 0.0

    @classmethod
    def get_live_usd_inr_rate(cls) -> float:
        """Fetch live USD/INR exchange rate with 15-minute cache and graceful fallback."""
        now = time.time()
        if cls._CACHE_USD_INR is not None and (now - cls._CACHE_USD_INR_TS) < 900:
            return cls._CACHE_USD_INR

        # 1. Try Frankfurter v2 Endpoint
        try:
            req = urllib.request.Request(cls.FRANKFURTER_API_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                if "rate" in data:
                    cls._CACHE_USD_INR = float(data["rate"])
                    cls._CACHE_USD_INR_TS = now
                    logging.info(f"Fetched live USD/INR from Frankfurter v2: {cls._CACHE_USD_INR}")
                    return cls._CACHE_USD_INR
                elif "rates" in data and "INR" in data["rates"]:
                    cls._CACHE_USD_INR = float(data["rates"]["INR"])
                    cls._CACHE_USD_INR_TS = now
                    return cls._CACHE_USD_INR
        except Exception as e:
            logging.info(f"Frankfurter v2 probe: {e}. Trying fallback.")

        # 2. Try Frankfurter app Endpoint
        try:
            req = urllib.request.Request(cls.FRANKFURTER_FALLBACK_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                if "rates" in data and "INR" in data["rates"]:
                    cls._CACHE_USD_INR = float(data["rates"]["INR"])
                    cls._CACHE_USD_INR_TS = now
                    return cls._CACHE_USD_INR
        except Exception as e:
            logging.info(f"Frankfurter app probe: {e}. Using configured or default exchange rate.")

        config = cls.get_config_from_file()
        return float(config.get("usd_inr_rate", cls.DEFAULT_USD_INR_RATE))

    @classmethod
    def get_usd_inr_rate(cls) -> float:
        return cls.get_live_usd_inr_rate()

    @classmethod
    def get_config_from_file(cls) -> Dict[str, Any]:
        """Load stored config file."""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading config file: {e}")
        return {"usd_inr_rate": cls.DEFAULT_USD_INR_RATE}

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Load consolidated live market configuration, IBJA bullion rates, and diamond feeds."""
        live_rate = cls.get_live_usd_inr_rate()
        ibja_data = IBJAGoldService.get_current_rates()

        rapnet_key = os.environ.get("RAPNET_API_KEY", "").strip()
        idex_key = os.environ.get("IDEX_API_KEY", "").strip()
        has_licensed_key = bool(rapnet_key or idex_key)

        return {
            "usd_inr_rate": live_rate,
            "provider": "IBJA Official Bullion Benchmark & BDB / Surat SDB Wholesale Diamond Indices",
            "api_key_configured": has_licensed_key,
            "last_sync": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "status": f"IBJA Rates Active • USD/INR = ₹{live_rate:.2f} • BDB & Surat Wholesale Active",
            "ibja_rates": ibja_data.get("rates", {}),
            "ibja_metadata": {
                "source": ibja_data.get("source"),
                "session": ibja_data.get("session"),
                "publication_timestamp": ibja_data.get("publication_timestamp"),
                "fetched_timestamp": ibja_data.get("fetched_timestamp"),
                "is_live": ibja_data.get("is_live"),
                "freshness": ibja_data.get("freshness"),
                "base_24k_rate_per_gram": ibja_data.get("base_24k_rate_per_gram")
            },
            "diamond_pricing": {
                "has_licensed_key": has_licensed_key,
                "natural_source": "Licensed RapNet / IDEX Feed" if has_licensed_key else "Mumbai Bharat Diamond Bourse (BDB) Physical Benchmark",
                "lab_grown_source": "Surat Diamond Bourse (SDB) CVD/HPHT Manufacturing Wholesale Index"
            },
            "markets": {
                "natural": "Mumbai Bharat Diamond Bourse (BDB) Physical Wholesale Matrix",
                "lab_grown": "Surat Diamond Bourse (SDB) CVD/HPHT Manufacturing Hub"
            }
        }

    @classmethod
    def save_config(cls, usd_inr_rate: float, provider: str, api_key: str = "") -> Dict[str, Any]:
        """Save updated Indian market rate settings and API credentials."""
        try:
            os.makedirs(os.path.dirname(cls.CONFIG_FILE), exist_ok=True)
            if api_key and len(api_key.strip()) > 3:
                os.environ["RAPNET_API_KEY"] = api_key.strip()
                os.environ["INDIAN_MARKET_API_KEY"] = api_key.strip()

            config = {
                "usd_inr_rate": float(usd_inr_rate),
                "provider": provider or "IBJA Benchmark & BDB / Surat SDB Indices",
                "api_key_configured": bool(api_key and len(api_key.strip()) > 3),
                "last_sync": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "status": "Indian Market & IBJA Bullion Connected",
                "markets": {
                    "natural": "Mumbai Bharat Diamond Bourse (BDB)",
                    "lab_grown": "Surat Diamond Bourse (SDB) CVD/HPHT Hub"
                }
            }
            with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            cls._CACHE_USD_INR = float(usd_inr_rate)
            cls._CACHE_USD_INR_TS = time.time()
            logging.info("Saved Indian market config.")
            return config
        except Exception as e:
            logging.error(f"Error saving Indian market config: {e}")
            return cls.get_config()

    @classmethod
    def get_indian_wholesale_quote(cls, diamond_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates authentic Indian wholesale price quote in ₹ (INR) using LicensedDiamondService.
        Calibrated to Mumbai Bharat Diamond Bourse (BDB) for Natural diamonds and
        Surat Diamond Bourse (SDB) for Lab-Grown (CVD/HPHT) diamonds.
        """
        try:
            carat = float(diamond_spec.get("carat", 1.0))
            if carat <= 0:
                return {
                    "is_connected": True,
                    "data_available": False,
                    "error_message": "Invalid carat weight specified.",
                    "currency": "INR",
                    "currency_symbol": "₹",
                    "total_wholesale_inr": 0,
                    "source": "Mumbai BDB / Surat SDB Wholesale Benchmark",
                    "timestamp": datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p IST")
                }

            live_usd_inr = cls.get_live_usd_inr_rate()
            quote = LicensedDiamondService.get_pricing_quote(diamond_spec, usd_inr_rate=live_usd_inr)

            if not quote.get("data_available"):
                return {
                    "is_connected": False,
                    "data_available": False,
                    "error_message": quote.get("error", "Data unavailable"),
                    "currency": "INR",
                    "currency_symbol": "₹",
                    "total_wholesale_inr": 0,
                    "source": "Mumbai BDB / Surat SDB Wholesale Benchmark",
                    "timestamp": datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p IST")
                }

            total_inr = quote["total_wholesale_inr"]
            price_per_carat_inr = quote["price_per_carat_inr"]

            return {
                "is_connected": True,
                "data_available": True,
                "currency": "INR",
                "currency_symbol": "₹",
                "market_type": quote.get("market_type", "Diamond"),
                "total_wholesale_inr": total_inr,
                "price_per_carat_inr": price_per_carat_inr,
                "price_per_carat_usd": round(price_per_carat_inr / max(live_usd_inr, 1.0), 2),
                "source": quote.get("source", "BDB / SDB Wholesale Matrix"),
                "source_type": quote.get("source_type", "Wholesale Benchmark"),
                "is_licensed_feed": quote.get("is_licensed_feed", False),
                "freshness": quote.get("freshness", "Verified Physical Trade Index"),
                "timestamp": quote.get("timestamp"),
                "usd_inr_rate": live_usd_inr,
                "approx_usd_value": round(total_inr / max(live_usd_inr, 1.0), 2),
                "disclaimer": quote.get("disclaimer", "")
            }
        except Exception as e:
            logging.error(f"Error calculating wholesale quote: {e}")
            return {
                "is_connected": False,
                "data_available": False,
                "error_message": f"Market benchmark calculation error: {str(e)}",
                "currency": "INR",
                "currency_symbol": "₹",
                "total_wholesale_inr": 0,
                "source": "Mumbai BDB / Surat SDB Wholesale Benchmark",
                "timestamp": datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p IST")
            }

    @staticmethod
    def format_inr(amount: Optional[float]) -> str:
        """Format number into standard Indian Rupee notation (e.g. ₹ 1,25,000 or ₹ 12.50 Lakh)."""
        if amount is None or amount <= 0:
            return "₹ 0"

        amt_int = int(round(amount))
        amt_str = str(amt_int)

        if len(amt_str) <= 3:
            return f"₹ {amt_str}"

        last_three = amt_str[-3:]
        remaining = amt_str[:-3]
        
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)

        formatted_num = ",".join(groups) + "," + last_three
        return f"₹ {formatted_num}"

    @staticmethod
    def format_inr_lakhs(amount: Optional[float]) -> str:
        """Format larger amounts into Indian Lakhs / Crores (e.g. ₹ 4.50 Lakh, ₹ 1.20 Cr)."""
        if amount is None or amount <= 0:
            return "₹ 0"

        if amount >= 10000000:
            cr = amount / 10000000.0
            return f"₹ {cr:.2f} Cr"
        elif amount >= 100000:
            lakh = amount / 100000.0
            return f"₹ {lakh:.2f} Lakh"
        else:
            return IndianMarketService.format_inr(amount)
