from DiamondPricePrediction.component.data_ingestion import DataIngestion,Data_ingestion_config
from DiamondPricePrediction.component.data_transformation import DataTransformation,DataTransformationConfig
from DiamondPricePrediction.component.model_training import ModelTrainer

import os,sys
from DiamondPricePrediction.utils.exception import CustomException
from DiamondPricePrediction.utils.logger import logging

# obj =DataIngestion()
# obj.initiate_data_ingestion()

class traning_flow:
    def start_data_ingestion(self):
        obj =DataIngestion()
        train_path,test_path =obj.initiate_data_ingestion()
        return (train_path,test_path)
    
    def start_data_transformation(self):
        train_path,test_path =self.start_data_ingestion()
        obj =DataTransformation()
        x_train_arr,x_test_arr,y_train,y_test =obj.initiate_data_transformation(train_path,test_path)
        return(x_train_arr,x_test_arr,y_train,y_test)
    def start_model_traning(self):
        x_train_arr,x_test_arr,y_train,y_test=self.start_data_transformation()
        obj =ModelTrainer()
        best_fit_model_name ,max_r2_accuracy =obj.initiate_model_trainer( x_train_arr,x_test_arr,y_train,y_test)
    
obj1= traning_flow()
obj1.start_data_ingestion()
obj1.start_data_transformation()
obj1.start_model_traning()



