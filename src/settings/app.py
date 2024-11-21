from pydantic_settings import BaseSettings
from pydantic import Field 

class AppSettings(BaseSettings):
    host:str=Field(validation_alias='HOST', default='0.0.0.0')
    port:int=Field(validation_alias='PORT', default=8000)
    title:str=Field(validation_alias='TITLE', default='api server')
    version:str=Field(validation_alias='VERSION', default='0.1.0')
    description:str=Field(validation_alias='DESCRIPTION', default='async parallel rest api based on zeromq and asyncio')
    workers:int=Field(validation_alias='WORKERS', default=1)