import asyncio
import datetime
import sys
import traceback
from queue import Queue
from typing import Dict

import redis
from fastapi import Depends, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from r3almX_backend.auth_service.auth_utils import TokenData
from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_handler_utils import get_db, get_user_by_username
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.realtime_service.chat_service import get_user_from_token
from r3almX_backend.realtime_service.main import realtime


class Connection:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.connection_status_cache: Dict[str, str] = {}
        self.connection_sockets: Dict[str, WebSocket] = {}

    def connect(self, user_id):
        self.connection_status_cache[user_id] = "online"
        self.set_status_cache(user_id, "online")

    def disconnect(self, user_id):
        if user_id in self.connection_status_cache:
            del self.connection_status_cache[user_id]
        if user_id in self.connection_sockets:
            del self.connection_sockets[user_id]
        self.set_status_cache(user_id, "offline")

    def get_status_cache(self, user_id) -> Dict[str, str]:
        cached_status = self.redis_client.hgetall("user_status")
        return {
            user_id.decode(): status.decode()
            for user_id, status in cached_status.item()
        }

    def set_dnd(self, user_id):
        # class C: integer notif push (silent number increment)
        pass

    def is_connected(self, user_id) -> bool:
        return (
            user_id in self.connection_status_cache
            or user_id in self.connection_sockets
        )

    def get_status(self, user_id) -> str:
        return self.connection_status_cache.get(user_id, "offline")

    def set_status(self, user_id, status):
        if status in ["online", "offline", "dnd"]:
            self.connection_status_cache[user_id] = status
            self.set_status_cache(user_id, status)
            getattr(self, f"set_{status}")(user_id)

    def set_status_cache(self, user_id, status):
        self.redis_client.hset("user_status", user_id, status)


connection_manager = Connection()


@realtime.websocket("/connection")
async def connect(websocket: WebSocket, token: str, db=Depends(get_db)):
    # write a wholistic solution for connection so that we can send notif
    # we dont need a feedback websocket we need to just read the data from the client through this
    user = get_user_from_token(token, db)
    if user:
        await websocket.accept()

        connection_manager.connect(user.id)
        connection_manager.connection_sockets[user.id] = websocket
        last_activity = datetime.datetime.now()
        heartbeat_interval = 30
        expiry_timeout = 300
        try:
            while True:
                try:
                    if connection_manager.is_connected(user.id) is False:
                        connection_manager.connection_socket[str(user.id)] = websocket
                        connection_manager.set_status_cache(
                            connection_manager.get_status(user.id)
                        )
                    connection_change_request = await websocket.receive_json()

                    # through this we can just check for keys inside of the change request
                    if connection_change_request["status"]:
                        connection_manager.set_status(
                            user.id, connection_change_request["status"]
                        )
                except asyncio.TimeoutError:
                    try:
                        await websocket.send_text("ping")
                        await asyncio.wait_for(
                            websocket.receive_text(), timeout=heartbeat_interval / 2
                        )
                        last_activity = datetime.now()

                    except (asyncio.TimeoutError, WebSocketDisconnect):
                        if (
                            datetime.now() - last_activity
                        ).total_seconds() > expiry_timeout:
                            print(f"disconnecting user: {user.id} ")
                            await websocket.close()
                            connection_manager.disconnect(user.id)
                            break
        except WebSocketDisconnect:
            connection_manager.disconnect(user.id)
    else:
        return websocket.close(1001)
