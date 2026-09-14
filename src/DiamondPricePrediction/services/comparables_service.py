import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from DiamondPricePrediction.utils.logger import logging
from DiamondPricePrediction.services.indian_market_service import IndianMarketService

class ComparablesService:
    """
    High-Performance Real Database Comparables Engine.
    Queries 193,573 verified historical sales records.
    Converts and presents all benchmark metrics in Indian Rupee (₹).
    Explicitly flags all data as Historical Benchmark Data, never 'Live'.
    """

    _DATASET_CACHE: Optional[pd.DataFrame] = None
    DATA_SOURCE_NAME = "Verified Global Benchmark Records (193,573 sales)"

    CUT_RANKS = {"Fair": 1, "Good": 2, "Very Good": 3, "Premium": 4, "Ideal": 5, "Excellent": 5}
    COLOR_RANKS = {"J": 1, "I": 2, "H": 3, "G": 4, "F": 5, "E": 6, "D": 7}
    CLARITY_RANKS = {"I1": 1, "SI2": 2, "SI1": 3, "VS2": 4, "VS1": 5, "VVS2": 6, "VVS1": 7, "IF": 8, "FL": 9}

    @classmethod
    def load_dataset(cls) -> pd.DataFrame:
        """Load and cache the benchmark dataset."""
        if cls._DATASET_CACHE is None:
            data_path = os.path.join("artifacts", "raw.csv")
            if not os.path.exists(data_path):
                data_path = os.path.join("artifacts", "train.csv")
            
            logging.info(f"Loading comparables benchmark dataset from {data_path}")
            df = pd.read_csv(data_path)
            cls._DATASET_CACHE = df
            logging.info(f"Dataset cached with {len(df):,} records.")
        return cls._DATASET_CACHE

    @classmethod
    def find_comparables(
        cls,
        carat: float,
        cut: str,
        color: str,
        clarity: str,
        depth: Optional[float] = None,
        table: Optional[float] = None,
        max_results: int = 6
    ) -> Dict[str, Any]:
        """
        Finds matching diamond sales records from the historical benchmark database,
        calculates similarity score, and converts prices to INR (₹).
        """
        try:
            df = cls.load_dataset()
            usd_inr = IndianMarketService.get_usd_inr_rate()
            
            norm_cut = "Ideal" if cut in ["Excellent", "Ideal"] else cut

            # 1. First Tier Filter: Exact Cut, Color, Clarity with Carat window (+/- 12%)
            carat_min = round(carat * 0.88, 2)
            carat_max = round(carat * 1.12, 2)

            subset = df[
                (df["cut"] == norm_cut) &
                (df["color"] == color) &
                (df["clarity"] == clarity) &
                (df["carat"] >= carat_min) &
                (df["carat"] <= carat_max)
            ]

            # 2. Relax if sample is too small (< 8 records)
            expanded = False
            if len(subset) < 8:
                expanded = True
                carat_min_exp = round(carat * 0.80, 2)
                carat_max_exp = round(carat * 1.20, 2)
                subset = df[
                    (df["color"] == color) &
                    (df["clarity"] == clarity) &
                    (df["carat"] >= carat_min_exp) &
                    (df["carat"] <= carat_max_exp)
                ]

            # 3. If still empty, broaden to carat range
            if len(subset) == 0:
                subset = df[
                    (df["carat"] >= round(carat * 0.75, 2)) &
                    (df["carat"] <= round(carat * 1.25, 2))
                ]

            if len(subset) == 0:
                return {
                    "source": cls.DATA_SOURCE_NAME,
                    "sample_count": 0,
                    "statistics": None,
                    "comparables": [],
                    "insufficient_data": True,
                    "message": "Insufficient historical benchmark sales data for this exact specification."
                }

            # Convert prices to INR
            prices_usd = subset["price"].values
            prices_inr = prices_usd * usd_inr
            ppc_inr = (prices_inr / subset["carat"].values)

            stats = {
                "sample_count": int(len(subset)),
                "carat_range_min": float(subset["carat"].min()),
                "carat_range_max": float(subset["carat"].max()),
                "median_price_inr": float(np.median(prices_inr)),
                "p25_price_inr": float(np.percentile(prices_inr, 25)),
                "p75_price_inr": float(np.percentile(prices_inr, 75)),
                "min_price_inr": float(np.min(prices_inr)),
                "max_price_inr": float(np.max(prices_inr)),
                "median_ppc_inr": float(np.median(ppc_inr)),
                "median_price_usd": float(np.median(prices_usd))
            }

            # Similarity Scoring
            target_cut_rank = cls.CUT_RANKS.get(norm_cut, 4)
            target_color_rank = cls.COLOR_RANKS.get(color, 4)
            target_clarity_rank = cls.CLARITY_RANKS.get(clarity, 4)

            carat_diff = np.abs(subset["carat"] - carat) / max(carat, 0.01)
            cut_diff = np.abs(subset["cut"].map(cls.CUT_RANKS).fillna(3) - target_cut_rank) / 4.0
            color_diff = np.abs(subset["color"].map(cls.COLOR_RANKS).fillna(4) - target_color_rank) / 6.0
            clarity_diff = np.abs(subset["clarity"].map(cls.CLARITY_RANKS).fillna(4) - target_clarity_rank) / 7.0

            total_dist = carat_diff * 0.45 + cut_diff * 0.15 + color_diff * 0.20 + clarity_diff * 0.20
            similarity_pct = np.clip(100.0 * (1.0 - total_dist), 45.0, 99.5).round(1)

            subset_scored = subset.copy()
            subset_scored["similarity_score"] = similarity_pct
            subset_scored["distance"] = total_dist
            subset_scored["price_inr"] = subset_scored["price"] * usd_inr

            top_matches = subset_scored.sort_values(by=["distance", "similarity_score"], ascending=[True, False]).head(max_results)

            comparables_list = []
            for _, row in top_matches.iterrows():
                reasons = []
                if row["cut"] == norm_cut:
                    reasons.append(f"Cut: {row['cut']}")
                if row["color"] == color:
                    reasons.append(f"Color: {row['color']}")
                if row["clarity"] == clarity:
                    reasons.append(f"Clarity: {row['clarity']}")
                
                carat_d = round(row["carat"] - carat, 2)
                reasons.append(f"Carat: {row['carat']:.2f}ct (Δ {carat_d:+.2f})")

                comp_item = {
                    "carat": float(row["carat"]),
                    "cut": str(row["cut"]),
                    "color": str(row["color"]),
                    "clarity": str(row["clarity"]),
                    "depth": float(row["depth"]),
                    "table": float(row["table"]),
                    "price_inr": round(float(row["price_inr"])),
                    "price_inr_formatted": IndianMarketService.format_inr(float(row["price_inr"])),
                    "price_usd": float(row["price"]),
                    "similarity_score": float(row["similarity_score"]),
                    "rationale": " • ".join(reasons)
                }
                comparables_list.append(comp_item)

            return {
                "source": cls.DATA_SOURCE_NAME,
                "sample_count": stats["sample_count"],
                "filter_mode": "Expanded Window" if expanded else "Exact Tier Match",
                "statistics": stats,
                "comparables": comparables_list,
                "insufficient_data": False
            }

        except Exception as e:
            logging.error(f"Error in ComparablesService: {e}")
            return {
                "source": cls.DATA_SOURCE_NAME,
                "sample_count": 0,
                "statistics": None,
                "comparables": [],
                "insufficient_data": True,
                "error": str(e)
            }
