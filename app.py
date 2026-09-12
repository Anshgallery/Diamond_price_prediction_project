import os
import sys

from flask import Flask, request, render_template

from DiamondPricePrediction.utils.logger import logging
from DiamondPricePrediction.utils.exception import CustomException
from DiamondPricePrediction.pipeline.prediction import (
    Customdata,
    PredictionPipeline
)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home_page():
    return render_template("index.html")


# ============================================================
# TRAILS PAGE
# ============================================================

@app.route("/trails")
def trails():
    return render_template("trails.html")


# ============================================================
# PREDICTION PAGE
# ============================================================

@app.route("/predict", methods=["GET", "POST"])
def predict():

    # --------------------------------------------------------
    # GET REQUEST
    # --------------------------------------------------------

    if request.method == "GET":

        return render_template("form.html")


    # --------------------------------------------------------
    # POST REQUEST
    # --------------------------------------------------------

    try:

        # ====================================================
        # 1. GET USER INPUT
        # ====================================================

        data = Customdata(

            carat=float(
                request.form.get("carat")
            ),

            depth=float(
                request.form.get("depth")
            ),

            table=float(
                request.form.get("table")
            ),

            x=float(
                request.form.get("x")
            ),

            y=float(
                request.form.get("y")
            ),

            z=float(
                request.form.get("z")
            ),

            cut=request.form.get("cut"),

            color=request.form.get("color"),

            clarity=request.form.get("clarity")
        )


        # ====================================================
        # 2. CONVERT USER INPUT INTO DATAFRAME
        # ====================================================

        fetched_df = data.get_data_as_dataframe()


        # ====================================================
        # 3. CREATE PREDICTION PIPELINE
        # ====================================================

        prediction_pipeline = PredictionPipeline()


        # ====================================================
        # 4. PREDICT DIAMOND PRICE
        # ====================================================

        result_predicted_arr = prediction_pipeline.prediction(
            fetched_df
        )


        # Get first prediction

        result = round(
            float(result_predicted_arr[0]),
            2
        )


        # ====================================================
        # 5. GET AI / SHAP EXPLANATION
        # ====================================================

        explanation = prediction_pipeline.explain_prediction(
            fetched_df
        )


        # ====================================================
        # 6. SEND RESULT TO HTML
        # ====================================================

        return render_template(

            "result.html",

            result=result,

            explanation=explanation

        )


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        logging.error(
            "Error occurred during prediction"
        )

        raise CustomException(
            e,
            sys
        )


# ============================================================
# RUN FLASK APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="0.0.0.0",

        port=8080

    )