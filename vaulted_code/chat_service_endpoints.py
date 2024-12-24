import asyncio
from queue import Queue
from typing import Dict

from fastapi import Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from sqlalchemy.orm import sessionmaker

from r3almX_backend.auth_service.auth_utils import TokenData
from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_handler_utils import get_db, get_user_by_username
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.chat_service.main import chat_service


def get_user_from_token(token: str, db) -> User:
    payload = jwt.decode(
        token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
    )
    username: str = payload.get("sub")
    token_data = TokenData(username=username)
    user = get_user_by_username(db, username=token_data.username)
    return user


class RoomHandler:
    def __init__(
        self,
        room_id: str,
    ) -> None:

        self.queue: Queue = Queue()
        self.room_id: str = room_id
        self.users: list[WebSocket] = []

    async def enqueue(self, message: str, user: str) -> None:
        """this method exposes our queue so
        that we can enqueue messages being received"""
        await self.queue.put((message, user))

    async def broadcast(self) -> None:
        """this method goes through our queue and pushes messages to the room and every user inside that room"""
        while True:
            message, _ = await self.queue.get()
            for users in self.users:
                await users.send_text(message)

    def digest(self) -> None:
        """limit of 10 messages in the queue, once queue is 10, we dispatch to db"""
        ...

    def connect_user(self, user_socket: WebSocket) -> None:
        self.users.append(user_socket)

    def disconnect_user(self, user_socket: WebSocket) -> None:
        self.users.remove(user_socket)


class WebSocketWorker:
    def __init__(self) -> None:
        self.room_instances: Dict[str, RoomHandler] = {}

    async def spawn(self, room_id, websocket: WebSocket) -> None:
        new_socket = RoomHandler(room_id)
        new_socket.connect_user(websocket)
        self.room_instances[room_id] = new_socket
        asyncio.create_task(new_socket.broadcast())

    def intake(self, room_id: str, message: str, user: str) -> None:
        self.room_instances[room_id].enqueue(message, user)

    def has(self, room_id: str) -> bool:
        try:
            if self.room_instances[room_id] != None:
                return True
        except KeyError:
            return False

    def get_all_data_recursive(self, dictionary):
        data = {}
        for key, value in dictionary.items():
            if isinstance(value, dict):
                data[key] = self.get_all_data_recursive(value)
            elif isinstance(value, RoomHandler):
                room_data = {
                    "queue_size": value.queue.qsize(),
                    "room_id": value.room_id,
                    "users connected": len(value.users),
                    "users": [str(user) for user in value.users],
                }
                data[key] = room_data
        return data

    def get_all_data(self):
        return self.get_all_data_recursive(self.room_instances)

    def disconnect_surface(self, websocket, room_id):
        self.room_instances[room_id].disconnect_user(websocket)


ws_worker = WebSocketWorker()


@chat_service.get("/message/rooms/")
def get_all_connections():
    return ws_worker.get_all_data()


@chat_service.websocket("/message/{room_id}")
async def broadcast_(
    websocket: WebSocket, room_id: str, token: str, db=Depends(get_db)
):
    user = get_user_from_token(token, db)
    if user:
        await websocket.accept()
        room_handler = ws_worker.room_instances.get(room_id)
        if room_handler is None:
            await ws_worker.spawn(room_id, websocket)
        else:
            room_handler.connect_user(websocket)
        try:
            while True:
                text_received = await websocket.receive_text()
                ws_worker.intake(room_id, text_received, user.id)
        except WebSocketDisconnect:
            ws_worker.disconnect_surface(websocket, room_id)
    else:
        return {"status": 500, "message": "there was an issue"}


# rabbitmq version queueing

import asyncio
import sys
import traceback
from typing import Dict

import aio_pika
from fastapi import Depends, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from r3almX_backend.auth_service.auth_utils import TokenData
from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_handler_utils import get_db, get_user_by_username
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.realtime_service.connection_service import NotificationSystem
from r3almX_backend.realtime_service.main import realtime

RABBITMQ_URL = "amqp://rabbitmq:rabbitmq@localhost:5672/"


def get_user_from_token(token: str, db) -> User:
    try:
        payload = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )
        username: str = payload.get("sub")
        token_data = TokenData(username=username)
        user = get_user_by_username(db, username=token_data.username)
        return user
    except JWTError:
        return None


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, set] = {}
        self.queues: Dict[str, aio_pika.Queue] = {}
        self.broadcast_tasks: Dict[str, asyncio.Task] = {}

    async def setup_rabbitmq(self, room_id: str):
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            queue_name = f"room_{room_id}"
            queue = await channel.declare_queue(queue_name)
            self.queues[room_id] = queue
            self.broadcast_tasks[room_id] = asyncio.create_task(self.broadcast(room_id))

    async def broadcast(self, room_id: str):
        room = self.rooms[room_id]
        queue = self.queues[room_id]
        try:
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        msg_body, user_id = message.body.decode().split(":")
                        for websocket in room:
                            await websocket.send_json({user_id: msg_body})
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print(f"Error in broadcast task for room {room_id}: {e}")
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout
            )

    async def add_message_to_queue(self, room_id: str, message: str, user_id: str):
        queue = self.queues[room_id]
        await queue.channel.default_exchange.publish(
            aio_pika.Message(body=f"{message}:{user_id}".encode()),
            routing_key=queue.name,
        )

    async def connect_user(self, room_id: str, websocket: WebSocket):
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
            await self.setup_rabbitmq(room_id)
        self.rooms[room_id].add(websocket)

    async def disconnect_user(self, room_id: str, websocket: WebSocket):
        room = self.rooms.get(room_id)
        if room:
            room.remove(websocket)
            if not room:
                del self.rooms[room_id]
                task = self.broadcast_tasks.pop(room_id)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass


room_manager = RoomManager()
notification_system = NotificationSystem()


@realtime.websocket("/message/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, room_id: str, token: str, db=Depends(get_db)
):
    user = get_user_from_token(token, db)
    if user:
        await websocket.accept()
        await room_manager.connect_user(room_id, websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await room_manager.add_message_to_queue(room_id, data, user.id)
                await notification_system.send_notification_to_user(
                    user.id, {"room_id": room_id, "data": data}
                )
        except WebSocketDisconnect:
            await room_manager.disconnect_user(room_id, websocket)
    else:
        await websocket.close(code=1008)


@realtime.get("/message/rooms/")
def get_all_connections():
    data = {}
    for room_id, room in room_manager.rooms.items():
        users = [str(websocket) for websocket in room]
        data[room_id] = {
            "users_connected": len(users),
            "users": users,
        }
    return data
