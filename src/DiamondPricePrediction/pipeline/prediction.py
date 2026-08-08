import os, sys
from DiamondPricePrediction.utils.exception import CustomException
from DiamondPricePrediction.utils.logger import logging
import pandas as pd
import numpy as np
import pickle


class PredictionPipeline:
    def __init__(self):
        pass

    def prediction(self, features):  # feature are dataframe
        try:
            preprocessor_path = os.path.join("artifacts", "preprocessor.pkl")
            model_path = "artifacts/best_model.pkl"

            with open(preprocessor_path, "rb") as f:
                preprocessor = pickle.load(f)

            with open(model_path, "rb") as f1:
                model = pickle.load(f1)

            scale_data = preprocessor.transform(
                features
            )  # encoding thing done here to make data perfect

            pred = model.predict(
                scale_data
            )  # jiss model ne sabse achi prediction di ha ab usko lo and fitt krdo like obj.predit(x_train)
            return pred

        except Exception as e:
            logging.info("problem in prediction_pipeline")
            raise CustomException(e, sys)


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
        clarity: str,
    ):  # independent  variable

        self.carat = carat
        self.depth = depth
        self.table = table
        self.x = x  # initializing the variable
        self.y = y
        self.z = z
        self.cut = cut
        self.color = color
        self.clarity = clarity

    def get_data_as_dataframe(self):
        try:
            custom_data_input_dict = {
                "carat": [self.carat],
                "depth": [self.depth],
                "table": [self.table],
                "x": [self.x],
                "y": [self.y],
                "z": [self.z],
                "cut": [self.cut],
                "color": [self.color],
                "clarity": [self.clarity],
            }
            # convert into dataframe
            df = pd.DataFrame(custom_data_input_dict)
            logging.info("Dataframe Gathered")
            return df
        except Exception as e:
            logging.info("Exception Occured in prediction pipeline in custom_data")
            raise CustomException(e, sys)
