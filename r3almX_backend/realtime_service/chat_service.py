import asyncio
import sys
import traceback
from typing import Dict, Set

import aio_pika
from fastapi import Depends, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from r3almX_backend.auth_service.auth_utils import TokenData
from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_handler_utils import get_db, get_user_by_username
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.realtime_service.connection_service import NotificationSystem
from r3almX_backend.realtime_service.main import realtime

rabbit_connection = None


async def get_rabbit_connection():
    """
    Establish a connection to the RabbitMQ server.
    :return: RabbitMQ connection object.
    """
    global rabbit_connection
    if not rabbit_connection or rabbit_connection.is_closed:
        rabbit_connection = await aio_pika.connect_robust(
            "amqp://rabbitmq:rabbitmq@localhost:5672/"
        )
    return rabbit_connection


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}
        self.rabbit_queues: Dict[str, aio_pika.Queue] = {}
        self.rabbit_channels: Dict[str, aio_pika.Channel] = {}
        self.broadcast_tasks: Dict[str, asyncio.Task] = {}

    async def broadcast(self, room_id: str):
        """
        Broadcasts messages to all users in a room.
        """
        try:
            # Retrieve the RabbitMQ queue for the specified room
            queue = self.rabbit_queues.get(room_id)
            if queue is None:
                print(f"Queue for room {room_id} is not initialized")
                return

            # Retrieve the set of WebSocket connections for the specified room
            room = self.rooms[room_id]

            # Iterate over messages in the RabbitMQ queue
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    # Process each message asynchronously
                    async with message.process():
                        # Decode the message body into user and data
                        user, data = message.body.decode().split(":", 1)

                        # Send the message to each WebSocket connection in the room
                        for websocket in room:
                            await websocket.send_text({user: data})
                            print(f"Sent message to websocket: {user}: {data}")
        except Exception as e:
            # Handle exceptions gracefully
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print(f"Error in broadcast task for room {room_id}: {e}")
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout
            )

    async def start_broadcast_task(self, room_id: str):
        if room_id not in self.broadcast_tasks:
            print(f"Starting broadcast task for room {room_id}")
            self.broadcast_tasks[room_id] = asyncio.create_task(self.broadcast(room_id))

    async def stop_broadcast_task(self, room_id: str):
        if room_id in self.broadcast_tasks:
            print(f"Stopping broadcast task for room {room_id}")
            task = self.broadcast_tasks.pop(room_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def add_message_to_queue(self, room_id: str, message: str, user: str):
        channel = self.rabbit_channels.get(room_id)
        if channel:
            await channel.default_exchange.publish(
                aio_pika.Message(body=f"{user}:{message}".encode()),
                routing_key=self.rabbit_queues[room_id].name,
            )
            print(
                f"Added message to queue {self.rabbit_queues[room_id].name}: {user}:{message}"
            )

    async def connect_user(self, room_id: str, websocket: WebSocket):
        room = self.rooms.get(room_id)
        if room is None:
            self.rooms[room_id] = set()
            connection = await get_rabbit_connection()
            channel = await connection.channel()
            queue = await channel.declare_queue(room_id, auto_delete=True)
            self.rabbit_queues[room_id] = queue
            self.rabbit_channels[room_id] = channel
            print(f"Declared queue for room {room_id}")
            await self.start_broadcast_task(room_id)
        self.rooms[room_id].add(websocket)
        print(f"User connected to room {room_id}")

    async def disconnect_user(self, room_id: str, websocket: WebSocket):
        room = self.rooms.get(room_id)
        if room:
            room.remove(websocket)
            if not room:
                del self.rooms[room_id]
                await self.rabbit_queues[room_id].delete()
                del self.rabbit_queues[room_id]
                await self.stop_broadcast_task(room_id)
                print(f"Deleted queue and stopped task for room {room_id}")


room_manager = RoomManager()
notification_system = NotificationSystem()


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
        return None


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
async def get_all_connections():
    data = {}
    for room_id, room in room_manager.rooms.items():
        queue_size = 0
        if room_id in room_manager.rabbit_queues:
            queue = room_manager.rabbit_queues[room_id]
            channel = room_manager.rabbit_channels[room_id]
            queue_state = await channel.declare_queue(room_id, passive=True)
            queue_size = queue_state.message_count
        users = [str(websocket) for websocket in room]
        data[room_id] = {
            "queue_size": queue_size,
            "users_connected": len(users),
            "users": users,
        }
    return data
