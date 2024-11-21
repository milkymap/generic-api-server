import zmq 
import zmq.asyncio as aiozmq 
import json 

from fastapi import APIRouter, Depends, HTTPException, status 

from ..manager import Manager
from .index_schema import CheckIndexResponse

from typing_extensions import Annotated
from src.backend.strategy import ConsumeResponse

from fastapi.responses import JSONResponse

class Index(APIRouter):
    def __init__(self, manager:Manager):
        super(Index, self).__init__()
        self.manager = manager
        super().add_api_route(path='/check', endpoint=self.check_index, methods=['GET'], response_model=CheckIndexResponse)
        super().add_api_route(path='/embedding', endpoint=self.embedding(), methods=['POST'], response_model=ConsumeResponse)

    async def check_index(self):
        return CheckIndexResponse(
            status=True,
            message='server is ready'
        )
    
    def embedding(self):
        try:
            socket_creator = self.manager.create_socket(
                socket_method='connect', socket_type=zmq.DEALER,
                addr='ipc:///tmp/frontend.worker.ipc'
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
        async def inner_embedding(query:str, socket:aiozmq.Socket=Depends(socket_creator)):
            await socket.send_multipart([b'', query.encode('utf-8')])
            has_data = await self.manager.wait_socket_response(socket, 5)
            if not has_data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail='no data was detected during socket-poll'
                )
            
            _, socket_response = await socket.recv_multipart()
            consume_response_data = json.loads(socket_response.decode('utf-8'))
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=consume_response_data
            )
            
        return inner_embedding
