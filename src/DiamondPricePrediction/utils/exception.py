import sys 
class CustomException(Exception):

    def __init__(self,error_message,error_details:sys):
        
        super().__init__(error_message)
        self.error_message =error_message
        _,_,exc_tb =error_details.exc_info()
        self.line_number = exc_tb.tb_lineno
        self.file_path =exc_tb.tb_frame.f_code.co_filename


        
    def __str__(self):
        return f"error in line {self.line_number},file : {self.file_path},message :{self.error_message}"
        

if __name__ =="__main__":
    try :
        a =10/0
    except Exception as e :
        raise CustomException(e,sys)



