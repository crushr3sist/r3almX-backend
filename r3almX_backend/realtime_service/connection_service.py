import asyncio
import datetime
from typing import Dict

import redis
from fastapi import Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_handler_utils import get_db, get_user_by_email
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.realtime_service.main import realtime


async def get_user_from_token(token: str, db) -> User:
    try:
        payload: dict = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )
        email: str = payload.get("sub")
        user = await get_user_by_email(db, email=email)
        return user
    except JWTError as j:
        return j


class Connection:
    def __init__(self):
        self.redis_client = redis.Redis().from_url(
            url="redis://172.22.96.1:6379", decode_responses=True, db=0
        )
        self.connection_status_cache: Dict[str, str] = {}
        self.connection_sockets: Dict[str, WebSocket] = {}

    def connect(self, user_id):
        self.connection_status_cache[user_id] = "online"
        self.set_status_cache(user_id, "online")

    async def disconnect(self, user_id):
        print("offline was called")
        if user_id in self.connection_status_cache:
            del self.connection_status_cache[user_id]
        if user_id in self.connection_sockets:
            del self.connection_sockets[user_id]
        self.set_status_cache(user_id, "offline")

    def get_status_cache(self, user_id) -> Dict[str, str]:
        cached_status = self.redis_client.hgetall("user_status")
        return {user_id: status for user_id, status in cached_status.items()}

    def get_user_status(self, user_id) -> str:
        cached_status = self.redis_client.hget("user_status")
        return cached_status.value

    def is_connected(self, user_id) -> bool:
        return (
            user_id in self.connection_status_cache
            or user_id in self.connection_sockets
        )

    def get_status(self, user_id) -> str:
        return self.connection_status_cache.get(user_id, "online")

    def set_status(self, user_id, status):
        if status in ["online", "offline", "dnd", "idle"]:
            self.connection_status_cache[user_id] = status
            self.set_status_cache(user_id, status)
            getattr(self, f"set_{status}")(user_id)

    def set_status_cache(self, user_id, status):
        self.redis_client.hset("user_status", str(user_id), status)

    async def send_notification(self, user_id, message):
        websocket = self.connection_sockets.get(user_id)
        if websocket:
            await websocket.send_json({"sender": str(user_id), "message": message})


connection_manager = Connection()


class NotificationSystem:
    def __init__(self):
        self.types = {
            1: "RoomPost",
            2: "FriendRequest",
            3: "RoomInvitation",
            4: "DM",
        }
        self.connections = connection_manager

    def return_user(self, user_id):
        return self.connections.connection_cache_list.get(user_id)

    async def send_notification_to_user(self, user_id, message):
        await self.connections.send_notification(user_id, message)


async def send_periodic_status_update(websocket, user_id):
    try:
        while True:
            await asyncio.sleep(30)  # Send update every 30 seconds
            current_status = connection_manager.get_status(user_id)
            await websocket.send_json(
                {"type": "STATUS_UPDATE", "status": current_status}
            )
    except RuntimeError:
        pass


@realtime.get("/status/get")
async def get_status(token: str, db=Depends(get_db)):
    user = await get_user_from_token(token, db)
    cached_data = connection_manager.get_status(user.id)
    return JSONResponse(cached_data)


@realtime.post("/status/change")
async def update_status(token: str, new_status: str, db=Depends(get_db)):
    user = await get_user_from_token(token, db)
    connection_manager.set_status(user.id, new_status)
    return {"status": "200", "message": "status set"}


@realtime.websocket("/connection")
async def connect(websocket: WebSocket, token: str, db=Depends(get_db)):
    user = await get_user_from_token(token, db)
    if user:
        await websocket.accept()
        connection_manager.connect(str(user.id))
        connection_manager.connection_sockets[str(user.id)] = websocket
        initial_status = connection_manager.get_status(user.id)
        await websocket.send_json({"type": "STATUS_UPDATE", "status": initial_status})

        last_activity = datetime.datetime.now()
        heartbeat_interval = 30
        expiry_timeout = 100

        try:
            while True:
                asyncio.create_task(send_periodic_status_update(websocket, user.id))
                await websocket.send_json(
                    {"status": "200", "connection": "established"}
                )
                try:
                    if connection_manager.is_connected(user.id) is False:
                        connection_manager.connection_sockets[str(user.id)] = websocket
                        connection_manager.set_status_cache(
                            user.id, connection_manager.get_status(user.id)
                        )

                except asyncio.TimeoutError:
                    try:
                        await websocket.send_text("ping")
                        await asyncio.wait_for(
                            websocket.receive_text(), timeout=heartbeat_interval / 2
                        )
                        last_activity = datetime.datetime.now()
                    except (asyncio.TimeoutError, WebSocketDisconnect):
                        if (
                            datetime.datetime.now() - last_activity
                        ).total_seconds() > expiry_timeout:
                            print(f"disconnecting user: {user.id} ")
                            await websocket.close()
                            connection_manager.disconnect(user.id)
                            break
        except (WebSocketDisconnect, RuntimeError):
            await connection_manager.disconnect(user.id)
            return await websocket.close(1001)

    else:
        return await websocket.close(1001)


# Now to use the NotificationSystem to send a notification to a user:
notification_system = NotificationSystem()


async def notify_user(user_id, message):
    await notification_system.send_notification_to_user(user_id, message)
