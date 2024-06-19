import asyncio
import datetime
import json
import random
import string
import sys
import traceback
import uuid
from datetime import datetime
from typing import Dict

# aio_pika is a library for working with RabbitMQ message queues
import aio_pika

# Imports from FastAPI for handling WebSockets and dependency injection
from fastapi import Depends, WebSocket, WebSocketDisconnect

# Imports from jose for working with JSON Web Tokens (JWT)
from jose import JWTError, jwt
from sqlalchemy import Column, DateTime, ForeignKey, String, Table, insert
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Imports from the project's auth_service module
from r3almX_backend.auth_service.auth_utils import TokenData
from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_handler_utils import (
    get_db,
    get_user,
    get_user_by_username,
)
from r3almX_backend.auth_service.user_models import User

# Imports from the project's realtime_service module
from r3almX_backend.chat_service.channel_system.channel_utils import get_message_model
from r3almX_backend.database import *
from r3almX_backend.realtime_service.connection_service import NotificationSystem
from r3almX_backend.realtime_service.DigestionBroker import DigestionBroker
from r3almX_backend.realtime_service.main import realtime

# Global variable to store the RabbitMQ connection
rabbit_connection = None

async def get_rabbit_connection():

    global rabbit_connection
    # If the connection is None or closed, create a new connection
    if not rabbit_connection or rabbit_connection.is_closed:
        rabbit_connection = await aio_pika.connect_robust(
            "amqp://rabbitmq:rabbitmq@localhost:5672/"
        )
    return rabbit_connection


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



                
# Initialize DigestionBroker and pass db to set_db method
digestion_broker = DigestionBroker(batch_size=10, flush_interval=5)

# Pass the get_db function to start_flush_scheduler to set the db session
asyncio.create_task(digestion_broker.start_flush_scheduler())



class RoomManager:
    """
    Class to manage rooms and handle messaging between connected clients.
    """

    def __init__(self):
        """
        Initialize the RoomManager instance.
        """
        self.rooms: Dict[str, set] = {}
        self.rabbit_queues: Dict[str, aio_pika.Queue] = {}
        self.rabbit_channels: Dict[str, aio_pika.Channel] = {}
        self.broadcast_tasks: Dict[str, asyncio.Task] = {}

    async def broadcast(self, room_id: str):

        try:
            queue = self.rabbit_queues.get(room_id)
            if queue is None:
                print(f"Queue for room {room_id} is not initialized")
                return

            room = self.rooms[room_id]
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        message_received = json.loads(message.body.decode())
                        for websocket in room:
                            await websocket.send_json(
                                {
                                    "message": message_received["message"],
                                    "username": get_user(
                                        self.db, message_received["user"]
                                    ).username,
                                    "uid": message_received["user"],
                                    "time_stamp": datetime.now().strftime(
                                        "%Y-%m-%d %I:%M:%S %p"
                                    ),
                                    "mid": message_received["id"],
                                }
                            )
                            print(f"Sent message to websocket: {message_received["user"]}: {message_received["message"]}")

        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print(f"Error in broadcast task for room {room_id}: {e}\n")
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout
            )

    async def start_broadcast_task(self, room_id: str):

        if room_id not in self.broadcast_tasks:
            print(f"Starting broadcast task for room {room_id}\n")
            self.broadcast_tasks[room_id] = asyncio.create_task(self.broadcast(room_id))

    async def stop_broadcast_task(self, room_id: str):

        if room_id in self.broadcast_tasks:
            print(f"Stopping broadcast task for room {room_id}\n")
            task = self.broadcast_tasks.pop(room_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def add_message_to_queue(
        self, room_id: str, message: str, user: str, mid: str
    ):

        channel = self.rabbit_channels.get(room_id)
        message_data = {"user": str(user), "message": message['message'], "id": mid, "cid":message['channel_id']}
        if channel:
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(message_data).encode()),
                routing_key=self.rabbit_queues[room_id].name,
            )
            print(
                f"Added message to queue {self.rabbit_queues[room_id].name}: {user}:{message}, id:{mid}\n"
            )
            await digestion_broker.add_message( user,  message)

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
        print(f"User connected to room {room_id}\n")

    async def disconnect_user(self, room_id: str, websocket: WebSocket):
        room = self.rooms.get(room_id)
        if room:
            room.remove(websocket)
            if not room:
                del self.rooms[room_id]
                await self.stop_broadcast_task(room_id)

                queue = self.rabbit_queues[room_id]
                try:
                    await queue.close()  
                    await queue.purge()  
                    await queue.delete() 
                    print(f"Queue {room_id} successfully deleted.\n")
                except Exception as e:
                    print(f"Failed to delete queue {room_id}: {e}\n")

                del self.rabbit_queues[room_id]
                del self.rabbit_channels[room_id]
                print(f"Deleted queue and stopped task for room {room_id}\n")

    def set_db(self, db):
        self.db = db


room_manager = RoomManager()
notification_system = NotificationSystem()


@realtime.websocket("/message/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, room_id: str, token: str, db=Depends(get_db)
):
    user = get_user_from_token(token, db)
    print("{username:", user.username, ",")
    print("id:", user.id, ",")
    print("email:", user.email, "}")

    room_manager.set_db(db)
    digestion_broker.set_db(db)
    if user:
        await websocket.accept()
        await room_manager.connect_user(room_id, websocket)
        try:
            while True:
                data = await websocket.receive_json()
                mid = str(
                    (
                        lambda length=8: "".join(
                            random.choices(
                                string.ascii_lowercase + string.digits,
                                k=length,
                            )
                        )
                    )()
                )
                await room_manager.add_message_to_queue(room_id, data, user.id, mid)

                await notification_system.send_notification_to_user(
                    user.id, {"room_id": room_id, "mid": mid}
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
            queue_state = await channel.declare_queue(
                room_id, passive=True, durable=True, auto_delete=True
            )
            queue_size = queue_state.message_count
        users = [str(websocket) for websocket in room]
        data[room_id] = {
            "queue_size": queue_size,
            "users_connected": len(users),
            "users": users,
        }
    return data
