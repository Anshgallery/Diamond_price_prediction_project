from DiamondPricePrediction.utils.logger import logging
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from DiamondPricePrediction.utils.exception import CustomException
import sys,os
import pickle


class DataTransformationConfig:
    preprocessor_path =os.path.join("artifacts","preprocessor.pkl")



class DataTransformation:
    def __init__(self):
       self.config = DataTransformationConfig()

    def initiate_data_transformation(self,train_path,test_path):
        try:
            train_df = pd.read_csv(train_path)
            test_df =pd.read_csv(test_path)

            logging.info("train and test loaded succesfully ")

            preprocessor_store =self.get_transformed_data()

            x_train =train_df.drop(columns=["id","price"],axis =1)
            x_test = test_df.drop(columns=["id","price"],axis =1)
            y_train =train_df["price"]
            y_test =test_df["price"]

            x_train_arr =preprocessor_store.fit_transform(x_train)
            x_test_arr= preprocessor_store.transform(x_test)

            os.makedirs(os.path.dirname(self.config.preprocessor_path),exist_ok=True)
            
            with open(self.config.preprocessor_path,"wb")as f:
                pickle.dump(preprocessor_store,f)

    
            return (
                x_train_arr,x_test_arr,y_train,y_test
            )
            
            







        except Exception as e:
            logging.info("error found in initiate_data_transformation")
            raise CustomException(e,sys)


    def get_transformed_data(self):
        try :
            logging.info("Data_transformation_initiated")
            cut_categories = ['Fair', 'Good', 'Very Good','Premium','Ideal']
            color_categories = ['D', 'E', 'F', 'G', 'H', 'I', 'J']
            clarity_categories = ['I1','SI2','SI1','VS2','VS1','VVS2','VVS1','IF']

            catagorical_col =['cut', 'color','clarity']
            numerical_col =['carat', 'depth','table', 'x', 'y', 'z'] # only independent


            # initiate pipelines
            catagorical_col_pipeline =Pipeline(
                steps=[
                    ("imputer",SimpleImputer(strategy = "most_frequent")),
                    
                    ("encodingbased_onrank",OrdinalEncoder(categories=[cut_categories,color_categories,clarity_categories])),
                ]
            )
            
            numerical_col_pipeline =Pipeline(
                steps =[
                   ("fill_null",SimpleImputer(strategy="median")),
                    ("standardization",StandardScaler())

                ]
            )

            preprocessor =ColumnTransformer(
                [
                   ("num_pipeline",numerical_col_pipeline,numerical_col),
                   ("catagorical_pipeline",catagorical_col_pipeline,catagorical_col)
                ]
            )
            

            return preprocessor
        except Exception as e:
            logging.info("exception_occur_in_get_transformation")
            raise CustomException(e,sys)