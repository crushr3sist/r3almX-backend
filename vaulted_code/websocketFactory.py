import abc
import asyncio
import sys
import traceback
from queue import Queue
from typing import Dict, Set

from fastapi import WebSocket


class WebSocketFactory(abc.ABC):
    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}
        self.queues: Dict[str, Queue] = {}
        self.tasks: Dict[str, asyncio.Task] = {}

    async def add_connection(self, connection_id: str, websocket: WebSocket):
        if connection_id not in self.connections:
            self.connections[connection_id] = set()
            self.queues[connection_id] = Queue()
            self.tasks[connection_id] = asyncio.create_task(
                self.broadcast_task(connection_id)
            )
        self.connections[connection_id].add(websocket)

    async def remove_connection(self, connection_id: str, websocket: WebSocket):
        if connection_id in self.connections:
            self.connections[connection_id].remove(websocket)
            if not self.connection[connection_id]:
                del self.connections[connection_id]
                del self.queues[connection_id]
                task = self.tasks.pop(connection_id)
                task.cancel()
                await task

    def add_to_queue(self, connection_id: str, data):
        if connection_id in self.queues:
            self.queues[connection_id].put_nowait(data)

    @abc.abstractmethod
    def broadcast_task(self, connection_id, data):
        pass
