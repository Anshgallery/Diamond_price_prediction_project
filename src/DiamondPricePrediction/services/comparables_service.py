import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from DiamondPricePrediction.utils.logger import logging

class ComparablesService:
    """
    High-Performance Real Database Comparables Engine.
    Queries the 193,573 real diamond records from the benchmark dataset.
    Calculates empirical distribution statistics and similarity ranking.
    Explicitly flags all data as Historical Benchmark Data, never 'Live'.
    """

    _DATASET_CACHE: Optional[pd.DataFrame] = None
    DATA_SOURCE_NAME = "Historical Benchmark Dataset (193,573 Verified Records)"

    CUT_RANKS = {"Fair": 1, "Good": 2, "Very Good": 3, "Premium": 4, "Ideal": 5}
    COLOR_RANKS = {"J": 1, "I": 2, "H": 3, "G": 4, "F": 5, "E": 6, "D": 7}
    CLARITY_RANKS = {"I1": 1, "SI2": 2, "SI1": 3, "VS2": 4, "VS1": 5, "VVS2": 6, "VVS1": 7, "IF": 8}

    @classmethod
    def load_dataset(cls) -> pd.DataFrame:
        """Load and cache the benchmark dataset."""
        if cls._DATASET_CACHE is None:
            data_path = os.path.join("artifacts", "raw.csv")
            if not os.path.exists(data_path):
                data_path = os.path.join("artifacts", "train.csv")
            
            logging.info(f"Loading comparables benchmark dataset from {data_path}")
            df = pd.read_csv(data_path)
            # Ensure price per carat column is computed
            df["price_per_carat"] = (df["price"] / df["carat"]).round(2)
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
        max_results: int = 8
    ) -> Dict[str, Any]:
        """
        Finds the closest matching real diamond records from the historical benchmark database.
        Returns statistical summary and top ranked individual comparables with similarity rationale.
        """
        try:
            df = cls.load_dataset()
            
            # Normalize cut name for lookup
            norm_cut = "Ideal" if cut in ["Excellent", "Ideal"] else cut

            # 1. First Tier Filter: Exact Cut, Color, Clarity with tight Carat window (+/- 12%)
            carat_min = round(carat * 0.88, 2)
            carat_max = round(carat * 1.12, 2)

            subset = df[
                (df["cut"] == norm_cut) &
                (df["color"] == color) &
                (df["clarity"] == clarity) &
                (df["carat"] >= carat_min) &
                (df["carat"] <= carat_max)
            ]

            # 2. Relax if sample is too small (< 10 records)
            expanded = False
            if len(subset) < 10:
                expanded = True
                carat_min_exp = round(carat * 0.80, 2)
                carat_max_exp = round(carat * 1.20, 2)
                subset = df[
                    (df["color"] == color) &
                    (df["clarity"] == clarity) &
                    (df["carat"] >= carat_min_exp) &
                    (df["carat"] <= carat_max_exp)
                ]

            # 3. If still empty (very rare or exotic diamond), broaden color/clarity window
            if len(subset) == 0:
                carat_min_broad = round(carat * 0.75, 2)
                carat_max_broad = round(carat * 1.25, 2)
                subset = df[
                    (df["carat"] >= carat_min_broad) &
                    (df["carat"] <= carat_max_broad)
                ]

            if len(subset) == 0:
                return {
                    "source": cls.DATA_SOURCE_NAME,
                    "sample_count": 0,
                    "statistics": None,
                    "comparables": [],
                    "insufficient_data": True,
                    "message": "Insufficient verified market data in historical benchmark for this exact diamond specification."
                }

            # Calculate Distribution Statistics
            prices = subset["price"].values
            ppc_values = subset["price_per_carat"].values

            stats = {
                "sample_count": int(len(subset)),
                "carat_range_min": float(subset["carat"].min()),
                "carat_range_max": float(subset["carat"].max()),
                "min_price": float(np.min(prices)),
                "p25_price": float(np.percentile(prices, 25)),
                "median_price": float(np.median(prices)),
                "p75_price": float(np.percentile(prices, 75)),
                "max_price": float(np.max(prices)),
                "avg_price_per_carat": float(np.mean(ppc_values)),
                "median_price_per_carat": float(np.median(ppc_values)),
                "p25_price_per_carat": float(np.percentile(ppc_values, 25)),
                "p75_price_per_carat": float(np.percentile(ppc_values, 75))
            }

            # Calculate similarity score for each row in subset
            target_cut_rank = cls.CUT_RANKS.get(norm_cut, 3)
            target_color_rank = cls.COLOR_RANKS.get(color, 4)
            target_clarity_rank = cls.CLARITY_RANKS.get(clarity, 4)

            # Vectorized similarity distance
            carat_diff = np.abs(subset["carat"] - carat) / max(carat, 0.01)
            cut_diff = np.abs(subset["cut"].map(cls.CUT_RANKS).fillna(3) - target_cut_rank) / 4.0
            color_diff = np.abs(subset["color"].map(cls.COLOR_RANKS).fillna(4) - target_color_rank) / 6.0
            clarity_diff = np.abs(subset["clarity"].map(cls.CLARITY_RANKS).fillna(4) - target_clarity_rank) / 7.0

            table_diff = np.abs(subset["table"] - (table or 57.0)) / 20.0
            depth_diff = np.abs(subset["depth"] - (depth or 61.7)) / 20.0

            total_dist = (
                carat_diff * 0.40 +
                cut_diff * 0.15 +
                color_diff * 0.15 +
                clarity_diff * 0.15 +
                table_diff * 0.075 +
                depth_diff * 0.075
            )

            similarity_pct = np.clip(100.0 * (1.0 - total_dist), 40.0, 99.9).round(1)

            subset_scored = subset.copy()
            subset_scored["similarity_score"] = similarity_pct
            subset_scored["distance"] = total_dist

            # Sort by highest similarity, take top N
            top_matches = subset_scored.sort_values(by=["distance", "similarity_score"], ascending=[True, False]).head(max_results)

            comparables_list = []
            for _, row in top_matches.iterrows():
                # Generate explanation why it's comparable
                reasons = []
                if row["cut"] == norm_cut:
                    reasons.append(f"Identical Cut ({row['cut']})")
                if row["color"] == color:
                    reasons.append(f"Identical Color ({row['color']})")
                if row["clarity"] == clarity:
                    reasons.append(f"Identical Clarity ({row['clarity']})")
                
                carat_d = round(row["carat"] - carat, 2)
                if abs(carat_d) < 0.03:
                    reasons.append(f"Exact Carat Match (Δ {carat_d:+.2f}ct)")
                else:
                    reasons.append(f"Carat {row['carat']:.2f}ct (Δ {carat_d:+.2f}ct)")

                comp_item = {
                    "id": int(row.get("id", 0)),
                    "carat": float(row["carat"]),
                    "cut": str(row["cut"]),
                    "color": str(row["color"]),
                    "clarity": str(row["clarity"]),
                    "depth": float(row["depth"]),
                    "table": float(row["table"]),
                    "measurements": f"{row.get('x', 0):.2f} x {row.get('y', 0):.2f} x {row.get('z', 0):.2f} mm",
                    "price": float(row["price"]),
                    "price_per_carat": float(row["price_per_carat"]),
                    "similarity_score": float(row["similarity_score"]),
                    "rationale": " • ".join(reasons),
                    "data_source": "Historical Benchmark Dataset"
                }
                comparables_list.append(comp_item)

            return {
                "source": cls.DATA_SOURCE_NAME,
                "sample_count": stats["sample_count"],
                "filter_mode": "Expanded Carat Window" if expanded else "Exact 4Cs Tier",
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
                "error": str(e),
                "message": "Error processing comparable diamond query."
            }
