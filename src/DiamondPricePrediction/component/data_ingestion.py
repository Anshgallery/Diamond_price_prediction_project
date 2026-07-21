import pandas as pd
from DiamondPricePrediction.utils.logger import logging
import os
from sklearn.model_selection import train_test_split
from DiamondPricePrediction.utils.exception import CustomException
import sys 

class Data_ingestion_config:
    raw_path =os.path.join("artifacts","raw.csv")
    train_data_path = os.path.join("artifacts","train.csv")
    test_data_path =os.path.join("artifacts","test.csv")    





class DataIngestion:
    def __init__(self):
        self.config =Data_ingestion_config()
    def initiate_data_ingestion(self):
        logging.info("data_ingestion_started")

        try :
            #load data

            logging.info("loding_file ")
            data =pd.read_csv("notebook/train.csv")
            logging.info("data_loded_succesfully")
             
            # make directory  and load it in  artifacts
            
            os.makedirs(os.path.dirname(self.config.raw_path),exist_ok=True)
            data.to_csv(self.config.raw_path,index=False)
            logging.info("perform train test split ")

            data_train ,data_test =train_test_split(data,test_size=0.20,train_size=0.80,random_state=42)

            os.makedirs(os.path.dirname(self.config.train_data_path),exist_ok=True)
            data_train.to_csv(self.config.train_data_path,index=False)

            os.makedirs(os.path.dirname(self.config.test_data_path),exist_ok=True)
            data_test.to_csv(self.config.test_data_path,index=False)
            logging.info("completed artifacts file ")
            logging.info("data_ingestion_part_completed")

            return(self.config.train_data_path,self.config.test_data_path)
        
        except Exception as e:
            # logging.info("problem in data ingestion")
            raise CustomException(e,sys)
            
if __name__ == "__main__":

    try:

        obj = DataIngestion()

        train_path, test_path = obj.initiate_data_ingestion()

        print("Train path:", train_path)
        print("Test path:", test_path)

    except Exception as e:

        print(e)








        
        
