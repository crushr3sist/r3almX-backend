import asyncio
import sys
import traceback
from queue import Queue
from typing import Dict

from fastapi import Depends, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from r3almX_backend.auth_service.auth_utils import TokenData
from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_handler_utils import get_db, get_user_by_username
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.chat_service.main import chat_service


def get_user_from_token(token: str, db) -> User:

    try:
        payload = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )
        username: str = payload.get("sub")
        token_data = TokenData(username=username)
        user = get_user_by_username(db, username=token_data.username)
        return user
    except JWTError as j:
        return j


class RoomManager:

    def __init__(self):

        self.rooms: Dict[str, set] = {}
        self.message_queues: Dict[str, Queue] = {}
        self.broadcast_tasks: Dict[str, asyncio.Task] = {}

    async def broadcast(self, room_id: str):

        try:
            queue = self.message_queues[room_id]
            room = self.rooms[room_id]
            while True:
                if not queue.empty():
                    message, user = queue.get_nowait()
                    for websocket in room:
                        await websocket.send_text(f"{user}: {message}")
                await asyncio.sleep(0.1)

        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print(f"Error in broadcast task for room {room_id}: {e}")
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout
            )

    async def start_broadcast_task(self, room_id: str):

        if room_id not in self.broadcast_tasks:
            self.broadcast_tasks[room_id] = asyncio.create_task(self.broadcast(room_id))

    async def stop_broadcast_task(self, room_id: str):

        if room_id in self.broadcast_tasks:
            task = self.broadcast_tasks.pop(room_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def add_message_to_queue(self, room_id: str, message: str, user: str):

        queue = self.message_queues.get(room_id)
        if queue:
            queue.put_nowait((message, user))

    async def connect_user(self, room_id: str, websocket: WebSocket):

        room = self.rooms.get(room_id)
        if room is None:
            self.rooms[room_id] = set()
            self.message_queues[room_id] = Queue()
            self.broadcast_tasks[room_id] = asyncio.create_task(self.broadcast(room_id))
        self.rooms[room_id].add(websocket)

    async def disconnect_user(self, room_id: str, websocket: WebSocket):

        room = self.rooms.get(room_id)
        if room:
            room.remove(websocket)
            if not room:
                del self.rooms[room_id]
                del self.message_queues[room_id]
                task = self.broadcast_tasks.pop(room_id)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass


room_manager = RoomManager()


@chat_service.websocket("/message/{room_id}")
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
                room_manager.add_message_to_queue(room_id, data, user.id)
                await room_manager.start_broadcast_task(room_id)
        except WebSocketDisconnect:
            await room_manager.disconnect_user(room_id, websocket)
    else:
        await websocket.close(code=1008)  # Unsupported data


@chat_service.get("/message/rooms/")
def get_all_connections():

    data = {}
    for room_id, room in room_manager.rooms.items():
        queue_size = room_manager.message_queues[room_id].qsize()
        users = [str(websocket) for websocket in room]
        data[room_id] = {
            "queue_size": queue_size,
            "users_connected": len(users),
            "users": users,
        }
    return data
