import os
import sys
import pickle
from urllib.parse import urlparse

import dagshub
import mlflow
import mlflow.sklearn

from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    root_mean_squared_error,
    mean_squared_error
)

from DiamondPricePrediction.utils.exception import CustomException


class ModelEvaluation:

    def __init__(self):
        pass

    # ---------------------------------------------------------
    # Calculate evaluation metrics
    # ---------------------------------------------------------
    def eval_metrics(self, ytest, y_predicted):

        rmse = root_mean_squared_error(
            ytest,
            y_predicted
        )

        mae = mean_absolute_error(
            ytest,
            y_predicted
        )

        mse = mean_squared_error(
            ytest,
            y_predicted
        )

        r2 = r2_score(
            ytest,
            y_predicted
        )

        return rmse, mae, mse, r2

    # ---------------------------------------------------------
    # Model Evaluation
    # ---------------------------------------------------------
    def initiate_model_evaluation(
        self,
        x_train_arr,
        x_test_arr,
        y_train,
        y_test
    ):

        try:

            # =================================================
            # 1. Load the best model from artifacts
            # =================================================

            path = os.path.join(
                "artifacts",
                "best_model.pkl"
            )

            with open(path, "rb") as f:
                model = pickle.load(f)

            print("Best model loaded successfully:")
            print(model)


            # =================================================
            # 2. Connect DagsHub with MLflow
            # =================================================

            dagshub.init(repo_owner='anshgallery',
                        repo_name='Diamond_price_prediction_project',
                        mlflow=True)



            # =================================================
            # 3. Get MLflow Tracking URI
            # =================================================

            tracking_uri = mlflow.get_tracking_uri()

            print(
                "MLflow Tracking URI:",
                tracking_uri
            )


            # =================================================
            # 4. Parse the Tracking URI
            # =================================================

            tracking_url_type_store = urlparse(
                tracking_uri
            ).scheme

            print(
                "Tracking URI type:",
                tracking_url_type_store
            )


            # =================================================
            # 5. Start MLflow Run
            # =================================================

            with mlflow.start_run():

                # -------------------------------------------------
                # Make predictions
                # -------------------------------------------------

                y_predicted = model.predict(
                    x_test_arr
                )


                # -------------------------------------------------
                # Calculate metrics
                # -------------------------------------------------

                rmse, mae, mse, r2 = self.eval_metrics(
                    y_test,
                    y_predicted
                )


                # -------------------------------------------------
                # Store metrics in dictionary
                # -------------------------------------------------

                metric = {
                    "rmse": rmse,
                    "mae": mae,
                    "mse": mse,
                    "r2": r2
                }


                # -------------------------------------------------
                # Log metrics to MLflow
                # -------------------------------------------------

                mlflow.log_metrics(
                    metric
                )


                # -------------------------------------------------
                # Log model name as parameter
                # -------------------------------------------------

                mlflow.log_param(
                    "model",
                    type(model).__name__
                )


                # =================================================
                # 6. Register model if MLflow is remote
                # =================================================

                if tracking_url_type_store != "file":

                    print(
                        "Remote MLflow detected."
                    )

                    mlflow.sklearn.log_model(
                        model,
                        "model",
                        registered_model_name="ml_model_dpp"
                    )

                    print(
                        "Model logged and registered successfully."
                    )


                # =================================================
                # 7. If MLflow is local
                # =================================================

                else:

                    print(
                        "Local MLflow detected."
                    )

                    mlflow.sklearn.log_model(
                        model,
                        "model"
                    )

                    print(
                        "Model logged successfully."
                    )


                # -------------------------------------------------
                # Print metrics
                # -------------------------------------------------

                print("\nModel Evaluation Results")
                print("-------------------------")
                print("RMSE:", rmse)
                print("MAE :", mae)
                print("MSE :", mse)
                print("R2  :", r2)


        except Exception as e:

            raise CustomException(
                e,
                sys
            )