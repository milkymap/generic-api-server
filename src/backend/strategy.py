from abc import ABC, abstractmethod
from typing import Any, Optional  


from pydantic import BaseModel

class ConsumeResponse(BaseModel):
    status:bool
    content:Any 
    exception:Optional[str]

class Strategy(ABC):
    def __init__(self, *strategy_args, **strategy_kwargs):
        pass 
    
    @abstractmethod
    def consume(self, data:bytes) -> Any:
        pass 

    def __call__(self, data:bytes) -> ConsumeResponse:
        try:
            content = self.consume(data)
            return ConsumeResponse(status=True, content=content, exception=None)
        except Exception as e:
            return ConsumeResponse(status=False, content=None,exception=str(e))

