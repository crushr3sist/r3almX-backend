from queue import Queue

from fastapi import Depends, WebSocket, WebSocketDisconnect

from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.chat_service.main import chat_service

""" 
this is where we connect users to channels
we need to write a **websocket handler** so multiple users
can poll messages in and out to certain channels

- write a feed websocket handler (client receiver)
- write a broadcast digest websocket handler (client  and message log updater)
- we need to specify which users to pool into which websocket
- we already specify the room id so the data knows where to be committed,
- we'll set a 50 message limit to be committed to the database 
    and stored in memory until committed
- and we'll poll whats being stored

"""


class RoomHandler:
    def __init__(self, room_socket: WebSocket) -> None:
        self.queue: Queue = []
        self.room_id: str
        self.room_socket: WebSocket = room_socket

    def enqueue(self, message: str, user: str):
        """this method exposes our queue so that we can enqueue messages being received"""
        ...

    def broadcast(self):
        """this method goes through our queue and pushes messages to the room and every user inside that room"""
        ...

    def digest(self):
        """this method pushes those messages to that specific rooms database"""
        ...

    def get_room_users(self):
        """aggregator for all users that are part of the room"""
        ...


class WebSocketWorker:
    def __init__(self) -> None:
        self.room_sockets: RoomHandler = []

    def spawn(self):
        """once a room is created, we spawn an instance for that room specifically"""
        new_socket = RoomHandler()
        self.room_sockets.append(new_socket)

    def intake(self):
        """feafawef"""
        ...


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)


manager = ConnectionManager()


@chat_service.websocket("/feed/{room_id}/ws")
async def broadcast_(
    websocket: WebSocket,
    room_id: str,
    token: str,
    db=Depends(get_db),
): ...


@chat_service.websocket("/feed/{room_id}/ws")
async def feed_ws_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str,
    db=Depends(get_db),
): ...


@chat_service.websocket("/feed/{room_id}/ws")
async def feed_ws_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str,
    db=Depends(get_db),
):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message text was: {data}", websocket)

    except WebSocketDisconnect:

        await manager.send_personal_message("Bye !!!", websocket)
        manager.disconnect(websocket)
