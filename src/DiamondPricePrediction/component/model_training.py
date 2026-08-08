from DiamondPricePrediction.utils.logger import logging
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from DiamondPricePrediction.utils.exception import CustomException
import sys, os, pickle

from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error,
    root_mean_squared_error,
)
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet


class ModelTrainer:
    def __init__(self):
        pass

    def initiate_model_trainer(self, x_train_arr, x_test_arr, y_train, y_test):
        try:

            logging.info("modeltraning started")
            model = [LinearRegression(), Ridge(), Lasso(), ElasticNet()]
            model_accuracy = []

            for i in model:
                i.fit(x_train_arr, y_train)
                ypredicted = i.predict(x_test_arr)

                r2 = r2_score(y_test, ypredicted)
                mae = mean_absolute_error(y_test, ypredicted)
                mse = mean_squared_error(y_test, ypredicted)
                rmse = root_mean_squared_error(y_test, ypredicted)

                model_accuracy.append(
                    {
                        "model": i,
                        "r2score": r2,
                        "mae": mae,
                        "msescore": mse,
                        "rmsescore": rmse,
                    }
                )
            best_fit_model = model_accuracy[0]
            for j in model_accuracy:
                if j["r2score"] > best_fit_model["r2score"]:
                    best_fit_model = j

            print("Best Model:", best_fit_model["model"])
            print("Best R2 Score:", best_fit_model)

            model_path = os.path.join("artifacts", "best_model.pkl")

            with open(model_path, "wb") as file:
                pickle.dump(best_fit_model["model"], file)

            return (best_fit_model, best_fit_model["r2score"])

        except Exception as e:
            raise CustomException(e, sys)
