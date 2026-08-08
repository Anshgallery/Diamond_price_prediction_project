from DiamondPricePrediction.pipeline.prediction import Customdata

obj = Customdata(0.32, 61.6, 58.0, 4.38, 4.41, 2.71, "Premium", "E", "SI1")
data = obj.get_data_as_dataframe()
print(data)  # converted dinto dataframe
