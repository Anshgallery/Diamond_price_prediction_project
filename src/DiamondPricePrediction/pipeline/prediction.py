import os
import sys
import pickle

import pandas as pd
import shap

from DiamondPricePrediction.utils.exception import CustomException
from DiamondPricePrediction.utils.logger import logging


class PredictionPipeline:

    def __init__(self):

        try:

            # =================================================
            # MODEL PATHS
            # =================================================

            preprocessor_path = os.path.join(
                "artifacts",
                "preprocessor.pkl"
            )

            model_path = os.path.join(
                "artifacts",
                "best_model.pkl"
            )

            # =================================================
            # LOAD PREPROCESSOR
            # =================================================

            with open(
                preprocessor_path,
                "rb"
            ) as f:

                self.preprocessor = pickle.load(f)

            # =================================================
            # LOAD TRAINED MODEL
            # =================================================

            with open(
                model_path,
                "rb"
            ) as f:

                self.model = pickle.load(f)

            logging.info(
                "Preprocessor and model loaded successfully"
            )

        except Exception as e:

            logging.info(
                "Error while loading model and preprocessor"
            )

            raise CustomException(
                e,
                sys
            )


    # =========================================================
    # NORMAL PRICE PREDICTION
    # =========================================================

    def prediction(self, features):

        try:

            # -------------------------------------------------
            # Transform input using saved preprocessor
            # -------------------------------------------------

            transformed_data = (
                self.preprocessor.transform(features)
            )

            # -------------------------------------------------
            # Predict price
            # -------------------------------------------------

            prediction = self.model.predict(
                transformed_data
            )

            logging.info(
                "Diamond price prediction completed"
            )

            return prediction

        except Exception as e:

            logging.info(
                "Problem in prediction pipeline"
            )

            raise CustomException(
                e,
                sys
            )


    # =========================================================
    # EXPLAINABLE AI - SHAP
    # =========================================================

    def explain_prediction(self, features):

        try:

            logging.info(
                "Starting SHAP explanation"
            )

            # =================================================
            # 1. LOAD TRAINING DATA
            # =================================================

            train_path = os.path.join(
                "artifacts",
                "train.csv"
            )

            train_df = pd.read_csv(
                train_path
            )

            logging.info(
                "Training data loaded for SHAP"
            )

            # =================================================
            # 2. REMOVE TARGET AND ID
            # =================================================

            background_df = train_df.drop(
                columns=[
                    "id",
                    "price"
                ],
                errors="ignore"
            )

            # =================================================
            # 3. TRANSFORM TRAINING DATA
            # =================================================

            background_transformed = (
                self.preprocessor.transform(
                    background_df
                )
            )

            # =================================================
            # 4. TRANSFORM USER INPUT
            # =================================================

            transformed_data = (
                self.preprocessor.transform(
                    features
                )
            )

            # =================================================
            # 5. GET FEATURE NAMES
            # =================================================

            feature_names = (
                self.preprocessor
                .get_feature_names_out()
            )

            # =================================================
            # 6. CREATE SHAP BACKGROUND
            # =================================================

            # Use first 100 training examples.
            # This keeps the web application fast.

            background_sample = (
                background_transformed[:100]
            )

            # =================================================
            # 7. CREATE SHAP EXPLAINER
            # =================================================

            explainer = shap.LinearExplainer(
                self.model,
                background_sample
            )

            # =================================================
            # 8. CALCULATE SHAP VALUES
            # =================================================

            shap_values = explainer.shap_values(
                transformed_data
            )

            # =================================================
            # 9. GET FIRST USER PREDICTION EXPLANATION
            # =================================================

            values = shap_values[0]

            # =================================================
            # 10. CREATE FEATURE EXPLANATION
            # =================================================

            explanation = []

            for name, value in zip(
                feature_names,
                values
            ):

                # Clean sklearn pipeline names

                clean_name = name.replace(
                    "num_pipeline__",
                    ""
                )

                clean_name = clean_name.replace(
                    "catagorical_pipeline__",
                    ""
                )

                explanation.append({

                    "feature": clean_name,

                    "impact": round(
                        float(value),
                        2
                    )

                })

            # =================================================
            # 11. SORT BY STRONGEST IMPACT
            # =================================================

            explanation.sort(
                key=lambda x: abs(
                    x["impact"]
                ),
                reverse=True
            )

            # =================================================
            # 12. RETURN TOP 5 FEATURES
            # =================================================

            top_features = explanation[:5]

            logging.info(
                "SHAP explanation generated successfully"
            )

            return top_features

        except Exception as e:

            logging.info(
                "Problem in SHAP explanation"
            )

            raise CustomException(
                e,
                sys
            )


# =============================================================
# CUSTOM DATA CLASS
# =============================================================

class Customdata:

    def __init__(
        self,
        carat: float,
        depth: float,
        table: float,
        x: float,
        y: float,
        z: float,
        cut: str,
        color: str,
        clarity: str
    ):

        self.carat = carat
        self.depth = depth
        self.table = table
        self.x = x
        self.y = y
        self.z = z
        self.cut = cut
        self.color = color
        self.clarity = clarity


    # =========================================================
    # CONVERT USER INPUT INTO DATAFRAME
    # =========================================================

    def get_data_as_dataframe(self):

        try:

            custom_data_input_dict = {

                "carat": [
                    self.carat
                ],

                "depth": [
                    self.depth
                ],

                "table": [
                    self.table
                ],

                "x": [
                    self.x
                ],

                "y": [
                    self.y
                ],

                "z": [
                    self.z
                ],

                "cut": [
                    self.cut
                ],

                "color": [
                    self.color
                ],

                "clarity": [
                    self.clarity
                ]

            }

            df = pd.DataFrame(
                custom_data_input_dict
            )

            logging.info(
                "User diamond data converted to DataFrame"
            )

            return df

        except Exception as e:

            logging.info(
                "Exception occurred while creating custom data"
            )

            raise CustomException(
                e,
                sys
            )