import os, sys
import pandas
from DiamondPricePrediction.utils.logger import logging
from DiamondPricePrediction.utils.exception import CustomException
from flask import Flask, request, render_template, jsonify
from DiamondPricePrediction.pipeline.prediction import Customdata, PredictionPipeline


app = Flask(
    __name__
)  # This creates your Flask application and stores it in the variable app.


@app.route("/")
def home_page():
    return render_template("index.html")


@app.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "GET":
        return render_template("form.html")
    else:
        data = Customdata(
            carat=float(request.form.get("carat")),
            depth=float(request.form.get("depth")),
            table=float(request.form.get("table")),
            x=float(request.form.get("x")),
            y=float(request.form.get("y")),
            z=float(request.form.get("z")),
            cut=request.form.get("cut"),
            color=request.form.get("color"),
            clarity=request.form.get("clarity"),
        )  # we just create a data object right now

        # Accesing the method available inside it
        fetched_df = data.get_data_as_dataframe()

        object = PredictionPipeline()  # This is pridictionpipeline class
        result_predicted_arr = object.prediction(fetched_df)  # we got the prediction
        result = round(
            result_predicted_arr[0], 2
        )  # we just fetch out the first element from the [0]
        return render_template("result.html", result=result)


if (
    __name__ == "__main__"
):  # "If I run this Python file directly, then start the Flask application."
    app.run(debug=True, host="0.0.0.0", port=8080)
