from pydantic import BaseModel

class LivenessResponse(BaseModel):
    status:bool
    message:str 