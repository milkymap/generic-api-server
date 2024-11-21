import asyncio 

import zmq 
import zmq.asyncio as aiozmq 
from asyncio import Lock, Event, Semaphore
from concurrent.futures import ThreadPoolExecutor

from src.log import logger 

from contextlib import asynccontextmanager, suppress
from operator import itemgetter, attrgetter

from typing import List, Dict, Tuple, Any, Optional, AsyncGenerator
from typing_extensions import Self 

from src.settings.manager import ManagerSettings

from async_timeout import timeout

from fastapi import HTTPException

from uuid import uuid4

class Manager:
    def __init__(self, manager_settings:ManagerSettings):
        self.manager_settings = manager_settings

    async def __aenter__(self) -> Self:
        self.ctx = aiozmq.Context()
        self.lock = Lock()
        self.event = Event()
        self.semaphore = Semaphore(value=self.manager_settings.semaphore_value)
        self.executor = ThreadPoolExecutor(max_workers=self.manager_settings.max_workers)
        return self 
    
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is not None: 
            logger.warning(exc_value)
            logger.exception(traceback)
        self.ctx.term()
        self.executor.shutdown(wait=True)

    def create_socket(self, socket_type:int, socket_method:str, addr:str):
        async def inner_create_socket() -> AsyncGenerator[aiozmq.Socket, None]:
            if socket_method not in ['bind', 'connect']:
                raise ValueError(f'{socket_method} must be one of [bind, connect]')
            
            socket = self.ctx.socket(socket_type=socket_type)
            initialized = 0 
            exception_val:Optional[Exception] = None
            try:
                attrgetter(socket_method)(socket)(addr=addr)
                initialized = 1
                logger.debug('socket initialized')
                yield socket 
            except Exception as e:
                logger.error(e)
                exception_val = e 
            finally:
                if initialized == 1:
                    socket.close(linger=0)
                    logger.debug('socket closed')

            if exception_val is not None:
                raise exception_val
        return inner_create_socket
    
    async def wait_socket_response(self, socket:aiozmq.Socket, delay:float=60) -> bool:
        current_task = asyncio.current_task()
        current_task.set_name(f'blocking-task-{str(uuid4())}')
        
        has_data:bool = False 
        with suppress(asyncio.TimeoutError, asyncio.CancelledError):
            async with timeout(delay=delay):
                while not has_data:
                    socket_polling_value = await socket.poll(timeout=1000)
                    if socket_polling_value != zmq.POLLIN:
                        continue
                    has_data = True 
        return has_data  

