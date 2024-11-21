import signal 
import asyncio 

from fastapi import FastAPI
from fastapi import BackgroundTasks, Depends, File, UploadFile, status, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from uvicorn import Server, Config 

from contextlib import asynccontextmanager

from src.settings.app import AppSettings
from src.log import logger 

from typing import List, Tuple, Dict 
from typing import Any, Optional

from .manager import Manager
from src.settings.manager import ManagerSettings

from .routers.index import Index

from .app_schema import LivenessResponse

class APPServer:
    def __init__(self, app_settings:AppSettings):
        self.app_settings = app_settings
        self.app = FastAPI(
            title=self.app_settings.title, version=self.app_settings.version, 
            description=self.app_settings.description, lifespan=self.lifespan
        )
        self.server = Server(
            config=Config(
                app=self.app, host=self.app_settings.host, 
                port=self.app_settings.port, workers=self.app_settings.workers)
        )

    async def liveness(self):
        return LivenessResponse(status=True, message='server is up and ready')

    async def release_resources(self):
        tasks:List[asyncio.Task] = asyncio.all_tasks()
        cancelled_tasks:List[asyncio.Task] = []
        for task in tasks:
            task_name = task.get_name()
            task2cancel = task_name.startswith('blocking-task-')
            if not task2cancel:
                continue
            task.cancel()
            cancelled_tasks.append(task)
        
        await asyncio.gather(*cancelled_tasks, return_exceptions=True)
        self.server.should_exit = True 

    @asynccontextmanager
    async def lifespan(self, app:FastAPI):
        loop = asyncio.get_running_loop()
        callback = lambda: asyncio.create_task(self.release_resources())
        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(sig, callback)
        logger.info('server process => init')
        app.add_api_route(path='/liveness', endpoint=self.liveness, methods=['GET'], response_model=LivenessResponse)
        yield 
        logger.info('server process => exit')
    
    async def listen(self, manager_settings:ManagerSettings):
        async with Manager(manager_settings=manager_settings) as manager:
            self.app.include_router(router=Index(manager=manager), prefix='/v1/index', tags=['index-manager'])
            await self.server.serve()


