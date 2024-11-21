from pydantic import BaseModel 

class CheckIndexResponse(BaseModel):
    status:bool 
    message:str 