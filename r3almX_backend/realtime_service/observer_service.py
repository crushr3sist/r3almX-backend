import asyncio
import hashlib
import json
from typing import Dict, Union, overload

import aio_pika
from fastapi import Depends, WebSocket, WebSocketDisconnect

from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.realtime_service.chat_service import RoomManager, room_manager
from r3almX_backend.realtime_service.main import realtime


class Observer:
    """metrics and state of the room's live service"""

    def __init__(self, room_inst: RoomManager):
        self.room_inst = room_inst

        self.rooms_hash: str = self.gen_hash(self.serialize(self.room_inst.rooms))

        self.rabbit_queues_hash: str = self.gen_hash(
            self.serialize(self.room_inst.rabbit_queues)
        )
        self.rabbit_channels_hash: str = self.gen_hash(
            self.serialize(self.room_inst.rabbit_channels)
        )
        self.broadcast_tasks_hash: str = self.gen_hash(
            self.serialize(self.room_inst.broadcast_tasks)
        )

    def gen_hash(self, dictionary):
        try:
            dict_hash = hashlib.md5()
            encoded = json.dumps(dictionary, sort_keys=True).encode()
            dict_hash.update(encoded)
            return dict_hash.hexdigest()
        except Exception as e:
            print(f"{e}")

    @overload
    def serialize(self, dict: Dict[str, set]):
        """serialize rooms"""
        ...

    @overload
    def serialize(self, dict: Dict[str, aio_pika.Queue]):
        """serialize queues"""
        ...

    @overload
    def serialize(self, dict: Dict[str, aio_pika.Channel]):
        """serialize channels"""
        ...

    @overload
    def serialize(self, dict: Dict[str, asyncio.Task]):
        """serialize broadcasts"""
        ...

    def serialize(
        self,
        dict: Dict[str, Union[set, aio_pika.Queue, aio_pika.Channel, asyncio.Task]],
    ):
        if all(isinstance(v, set) for v in dict.values()):
            return {
                key: {
                    "count": len(ws_set),
                    "connection_ids": [id(ws) for ws in ws_set],
                }
                for key, ws_set in dict.items()
            }

        elif all(isinstance(v, aio_pika.Queue) for v in dict.values()):
            return {
                key: {
                    "name": queue.name,
                    "durable": queue.durable,
                    "exclusive": queue.exclusive,
                    "auto_delete": queue.auto_delete,
                    "arguments": dict(queue.arguments) if queue.arguments else {},
                }
                for key, queue in dict.items()
            }

        elif all(isinstance(v, aio_pika.Channel) for v in dict.values()):

            return {
                key: {
                    "channel_number": channel.number,
                    "is_closed": channel.is_closed,
                    "connection_name": (
                        getattr(channel.connection, "name", "unknown")
                        if hasattr(channel, "connection")
                        else "unknown"
                    ),
                }
                for key, channel in dict.items()
            }

        elif all(isinstance(v, asyncio.Task) for v in dict.values()):
            return {
                key: {
                    "done": task.done(),
                    "cancelled": task.cancelled(),
                    "name": getattr(task, "_name", None) or "unnamed",
                    "coro_name": (
                        task.get_coro().__name__
                        if hasattr(task.get_coro(), "__name__")
                        else str(task.get_coro())
                    ),
                    "exception": (
                        str(task.exception())
                        if task.done() and task.exception()
                        else None
                    ),
                }
                for key, task in dict.items()
            }

    def update_check(self):

        _rooms_hash: str = self.gen_hash(self.serialize(self.room_inst.rooms))

        _rabbit_queues_hash: str = self.gen_hash(
            self.serialize(self.room_inst.rabbit_queues)
        )

        _rabbit_channels_hash: str = self.gen_hash(
            self.serialize(self.room_inst.rabbit_channels)
        )

        _broadcast_tasks_hash: str = self.gen_hash(
            self.serialize(self.room_inst.broadcast_tasks)
        )

        # individual if statements to update parts which need to updated
        # instead of waiting for every single piece of information to update

        if _rooms_hash == self.rooms_hash:
            self.rooms_hash = _rooms_hash

        if _rabbit_queues_hash == self.rabbit_queues_hash:
            self.rabbit_queues_hash = _rabbit_queues_hash

        if _rabbit_channels_hash == self.rabbit_channels_hash:
            self.rabbit_channels_hash = _rabbit_channels_hash

        if _broadcast_tasks_hash == self.broadcast_tasks_hash:
            self.broadcast_tasks_hash = _broadcast_tasks_hash

    def send(self):

        return {
            "rooms": self.serialize(self.room_inst.rooms),
            "rabbit_queues": self.serialize(self.room_inst.rabbit_queues),
            "rabbit_channels": self.serialize(self.room_inst.rabbit_channels),
            "broadcast_tasks": self.serialize(self.room_inst.broadcast_tasks),
        }


observer = Observer(room_inst=room_manager)

"""
 - username: oddyseys
 - password: password
"""


@realtime.websocket("/logs")
async def logs_endpoint(websocket: WebSocket, db=Depends(get_db)):
    # user: User | str = await get_user_from_token(token, db)
    # print(user)

    await websocket.accept()
    while True:
        try:
            await websocket.send_json(observer.send())
            await asyncio.sleep(1)  # Add delay to prevent spam

        except WebSocketDisconnect:
            break
    await WebSocket.close()
