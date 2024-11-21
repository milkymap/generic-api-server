from pydantic_settings import BaseSettings
from pydantic import Field 

class ManagerSettings(BaseSettings):
    max_workers:int=Field(validation_alias='MAX_WORKERS', default=32)
    semaphore_value:int=Field(validation_alias='SEMAPHORE_VALUE', default=128)
     
