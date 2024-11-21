import zmq 
import signal 
import multiprocessing as mp

import json 
from io import BytesIO

from src.log import logger 

from contextlib import suppress
from typing import List, Dict, Tuple, Optional, Type

from .strategy import Strategy, ConsumeResponse

class MessageQueue:
    def __init__(self, nb_workers:int, strategy_cls:Type[Strategy], *strategy_args, **strategy_kwargs):
        self.nb_workers = nb_workers
        self.strategy_cls = strategy_cls
        self.strategy_args = strategy_args
        self.strategy_kwargs = strategy_kwargs 

    def define_strategy(self) -> Strategy:
        return self.strategy_cls(*self.strategy_args, **self.strategy_kwargs) 

    def worker(self, worker_id:str, backend_addr:str):
        signal.signal(signal.SIGTERM, lambda signum, frame: signal.raise_signal(signal.SIGINT))

        strategy:Optional[Strategy] = None
        try:
            strategy = self.define_strategy()
        except Exception as e:
            logger.error(e)

        if strategy is None:
            logger.error(f'failed to initialized the strategy for worker {worker_id}') 
            exit(1)

        ctx = zmq.Context()

        dealer_socket:zmq.Socket = ctx.socket(zmq.DEALER)
        dealer_socket.connect(backend_addr)

        logger.info(f"Worker {worker_id} is ready to serve")
        dealer_socket.send_multipart([b"", b"READY", b"", b""])
        while True:
            try:
                incoming_signal = dealer_socket.poll(timeout=1000)
                if incoming_signal != zmq.POLLIN:
                    continue
                _, source_client_id, encoded_client_message = dealer_socket.recv_multipart()
                consume_response:ConsumeResponse = strategy(encoded_client_message)
                dealer_socket.send_multipart([b"", b"RESPONSE", source_client_id], flags=zmq.SNDMORE)
                dealer_socket.send_json(consume_response.model_dump())
                dealer_socket.send_multipart([b"", b"READY", b"", b""])  # signal that worker is ready
                logger.info(f"Worker {worker_id} has processed a request")
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(e)
                logger.exception(e)
                break 
    
        dealer_socket.close(linger=0)
        ctx.term()

    def broker(self, frontend_addr:str="ipc://frontend.ipc", backend_addr:str="ipc://backend.ipc"):
        ctx = zmq.Context()

        frontend_socket:zmq.Socket = ctx.socket(zmq.ROUTER)
        frontend_socket.bind(frontend_addr)
        backend_socket:zmq.Socket = ctx.socket(zmq.ROUTER)
        backend_socket.bind(backend_addr)

        workers:List[mp.Process] = []
        for i in range(self.nb_workers):
            worker = mp.Process(target=self.worker, args=(str(i), backend_addr))
            worker.start()
            workers.append(worker)
        
        worker_queue:List[bytes] = []
        poller = zmq.Poller()
        poller.register(frontend_socket, zmq.POLLIN)
        poller.register(backend_socket, zmq.POLLIN)

        logger.info("Broker is ready to serve")
        sigint_received = False
        while True:
            try:
                for worker in workers:
                    if not worker.is_alive():
                        break 

                sockets_hmap:Dict[zmq.Socket, int] = dict(poller.poll(timeout=1000))
                logger.info(f"Broker is polling with {len(worker_queue)} workers in the queue")
                if sockets_hmap.get(frontend_socket) == zmq.POLLIN:
                    if len(worker_queue) > 0:
                        source_client_id, _, encoded_client_message = frontend_socket.recv_multipart()
                        worker_id = worker_queue.pop(0)
                        backend_socket.send_multipart([worker_id, b"", source_client_id, encoded_client_message])
                
                if sockets_hmap.get(backend_socket) != zmq.POLLIN:
                    continue
                
                worker_id, _, message_event, source_client_id, encoded_worker_data = backend_socket.recv_multipart()
                if message_event == b"READY":
                    worker_queue.append(worker_id)
                    continue

                frontend_socket.send_multipart([source_client_id, b"", encoded_worker_data])
            except KeyboardInterrupt:
                sigint_received = True
                break
            except Exception as e:
                logger.error(e)
                logger.exception(e)
                break
        
        logger.info("Terminating workers")
        for worker in workers:
            if worker.is_alive() and not sigint_received:
                worker.terminate()
            worker.join()
        
        frontend_socket.close(linger=0)
        backend_socket.close(linger=0)
        ctx.term()


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            logger.error(exc_value)
            logger.exception(traceback)
        
