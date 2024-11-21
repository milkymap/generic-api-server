from .strategy import Strategy
from .message_queue import MessageQueue

from src.log import logger 
from typing import Union, List, Type  

from random import random
import multiprocessing as mp 

import json 

class Embedding(Strategy):
    def __init__(self, model_name:str, device:str):
        self.modle_name = model_name 
        self.device = device
        logger.info(f'initialize embedding with the model {model_name} on device {device}') 
    
    def consume(self, data:bytes) -> List[float]:
        sentence = data.decode('utf-8')
        print(sentence)
        if not isinstance(sentence, str):
            raise ValueError('input data must be a string')
        return [random() for _ in range(128)]
        
def start_backend(
        nb_workers:int, frontend_addr:str, backend_addr:str, 
        strategy_cls:Type[Strategy], *strategy_args, **strategy_kwargs
        ) -> mp.Process:
    assert issubclass(strategy_cls, Strategy), f"{strategy_cls} must be a subclass of abstract Strategy"
    def inner_process():
        mq = MessageQueue(
            nb_workers=nb_workers, strategy_cls=strategy_cls, 
            *strategy_args, **strategy_kwargs
        )
        mq.broker(
            frontend_addr=frontend_addr,
            backend_addr=backend_addr
        )
    
    process = mp.Process(target=inner_process, args=[])
    process.start()
    return process