from queue import Queue

from fastapi import Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from sqlalchemy.orm import sessionmaker

from r3almX_backend.auth_service.auth_utils import TokenData
from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_handler_utils import get_db, get_user_by_username
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.chat_service.main import chat_service


class RoomHandler:
    def __init__(
        self,
        room_id: str,
    ) -> None:

        self.queue: Queue = Queue()
        self.room_id: str
        self.users: WebSocket = []

    def enqueue(self, message: str, user: str) -> None:
        """this method exposes our queue so that we can enqueue messages being received"""
        self.queue.put((message, user))
        self.broadcast()

    async def broadcast(self) -> None:
        """this method goes through our queue and pushes messages to the room and every user inside that room"""

        for user in self.users:
            message_to_broadcast = self.queue.get()
            await user.send_text(message_to_broadcast[0])

    def digest(self) -> None:
        """limit of 10 messages in the queue, once queue is 10, we dispatch to db"""
        ...

    def connect_user(self, user_socket: WebSocket) -> None:
        self.users.append(user_socket)

    def disconnect_user(self, user_socket: WebSocket) -> None:
        self.users.remove(user_socket)


class WebSocketWorker:
    def __init__(self) -> None:
        # need to keep track of all the rooms that are currently active
        # @future need to implement room_socket into redis
        self.room_instances: dict[str, RoomHandler] = {}

    def spawn(self, room_id, websocket: WebSocket) -> None:
        """once a room is created, we spawn an instance for that room specifically"""
        new_socket = RoomHandler(room_id)
        new_socket.connect_user(websocket)
        self.room_instances[room_id] = new_socket

    def intake(self, room_id: str, message: str, user: str) -> None:
        """call the enqueue function"""
        self.room_instances[room_id].enqueue(message, user)

    def has(self, room_id: str) -> bool:
        try:
            if self.room_instances[room_id] != None:
                return True
        except KeyError:
            return False

    def disconnect_surface(self, websocket, room_id):
        self.room_instances[room_id].disconnect_user(websocket)


ws_worker = WebSocketWorker()


def get_user_from_token(token: str, db) -> User:
    payload = jwt.decode(
        token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
    )
    username: str = payload.get("sub")
    token_data = TokenData(username=username)
    user = get_user_by_username(db, username=token_data.username)
    return user


@chat_service.websocket("/message/{room_id}")
async def broadcast_(
    websocket: WebSocket, room_id: str, token: str, db=Depends(get_db)
):
    print(token)
    user = get_user_from_token(token, db)
    if user:
        await websocket.accept()
        try:
            while True:
                if not ws_worker.has(room_id):
                    ws_worker.spawn(room_id, websocket)
                text_received = await websocket.receive_text()
                print(text_received)
                ws_worker.intake(room_id, text_received, user.id)
        except WebSocketDisconnect:
            ws_worker.disconnect_surface(websocket, room_id)
    else:
        return {"status": 500, "message": "there was an issue"}


@chat_service.get("/message/rooms/")
def get_all_connections():
    return {
        "connections:": {
            str(list(ws_worker.room_sockets.keys())): str(
                list(ws_worker.room_sockets.values())
            )
        }
    }
