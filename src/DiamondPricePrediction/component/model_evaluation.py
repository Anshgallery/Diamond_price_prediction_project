import os 
import sys 
from sklearn.metrics import r2_score,mean_absolute_error,root_mean_squared_error,mean_squared_error
import mlflow
import mlflow.sklearn
import numpy as np
import pickle
from urllib.parse import urlparse
from DiamondPricePrediction.utils.exception import CustomException


class ModelEvaluation:
    def __init__(self):
        pass

    def eval_metrics(self,ytest,y_predicted):
        rmse =root_mean_squared_error(ytest,y_predicted)
        mae = mean_absolute_error(ytest,y_predicted)
        mse = mean_squared_error(ytest,y_predicted)
        r2 = r2_score(ytest,y_predicted)

        return(rmse,mae,mse,r2)
    
    def initiate_model_evaluation(self,x_train_arr, x_test_arr, y_train, y_test):

        try :
            # load the best model from artifacts
            path =os.path.join("artifacts","best_model.pkl")
            with open(path,"rb") as f:
                model= pickle.load(f)
            print(model)

            #connect wiht dagshub 

            mlflow.set_registry_uri("https://dagshub.com/Anshgallery/Diamond_price_prediction_project.mlflow") #
            #"MLflow, my Model Registry is located here on DagsHub."

            tracking_url_type_store=urlparse(mlflow.get_tracking_uri()).scheme
            # Breaks the MLflow tracking URL into parts like scheme, netloc, path, etc.
            # Then extracts only the scheme (https/http/file).
  

            


            with mlflow.start_run():
               y_predicted = model.predict(x_test_arr)
               rmse,mae,mse,r2 =self.eval_metrics(y_test,y_predicted)

               metric ={
                   "rmse":rmse ,
                    "mae":mae ,
                    "mse":mse,
                    "r2":r2

               }

               mlflow.log_metrics(metric) # stored in mlrun
               


        except Exception as e :

            raise CustomException(e,sys)

    
        





