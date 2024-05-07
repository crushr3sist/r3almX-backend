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
    """
    The function `get_user_from_token` decodes a JWT token to extract the username and retrieves the
    corresponding user from the database.

    :param token: A JWT token that contains user information
    :type token: str
    :param db: The `db` parameter in the `get_user_from_token` function likely refers to a database
    connection or object that is used to interact with the database where user information is stored.
    This parameter is essential for retrieving user data based on the token provided. It is expected to
    be an instance of a database
    :return: The function `get_user_from_token` is returning a `User` object.
    """
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
    # The `RoomManager` class initializes dictionaries to manage rooms, message queues, and broadcast
    # tasks.
    def __init__(self):

        self.rooms: Dict[str, set] = {}
        self.message_queues: Dict[str, Queue] = {}
        self.broadcast_tasks: Dict[str, asyncio.Task] = {}

    async def broadcast(self, room_id: str):
        """
        The `broadcast` function asynchronously sends messages from a queue to all websockets in a
        specified room.

        :param room_id: The `room_id` parameter in the `broadcast` method is a string that represents
        the unique identifier of the room for which messages are being broadcasted. This method is
        designed to continuously check for new messages in the message queue associated with the
        specified room and send those messages to all the connected websockets
        :type room_id: str
        """
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
        """
        This function starts a broadcast task for a specific room if it doesn't already exist.

        :param room_id: The `room_id` parameter in the `start_broadcast_task` method is a string that
        represents the unique identifier of the room for which the broadcast task is being started
        :type room_id: str
        """
        if room_id not in self.broadcast_tasks:
            self.broadcast_tasks[room_id] = asyncio.create_task(self.broadcast(room_id))

    async def stop_broadcast_task(self, room_id: str):
        """
        This Python function stops a broadcast task associated with a specific room ID by cancelling it.

        :param room_id: The `room_id` parameter in the `stop_broadcast_task` method is a string that
        represents the unique identifier of the room for which the broadcast task needs to be stopped.
        This method is designed to cancel and remove a broadcast task associated with the specified
        `room_id`
        :type room_id: str
        """
        if room_id in self.broadcast_tasks:
            task = self.broadcast_tasks.pop(room_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def add_message_to_queue(self, room_id: str, message: str, user: str):
        """
        The function adds a message to a queue associated with a specific room ID.

        :param room_id: The `room_id` parameter is a string that represents the unique identifier of the
        room where the message will be added to the queue
        :type room_id: str
        :param message: The `message` parameter is a string that represents the message that you want to
        add to the message queue for a specific room
        :type message: str
        :param user: The `user` parameter in the `add_message_to_queue` method represents the user who
        is sending the message to the specified room
        :type user: str
        """
        queue = self.message_queues.get(room_id)
        if queue:
            queue.put_nowait((message, user))

    async def connect_user(self, room_id: str, websocket: WebSocket):
        """
        This Python async function connects a user to a specified room by adding their WebSocket to the
        room's set of connections.

        :param room_id: The `room_id` parameter is a string that represents the identifier of the room
        to which the user is connecting
        :type room_id: str
        :param websocket: A WebSocket object representing the connection between the server and the
        client
        :type websocket: WebSocket
        """
        room = self.rooms.get(room_id)
        if room is None:
            self.rooms[room_id] = set()
            self.message_queues[room_id] = Queue()
            self.broadcast_tasks[room_id] = asyncio.create_task(self.broadcast(room_id))
        self.rooms[room_id].add(websocket)

    async def disconnect_user(self, room_id: str, websocket: WebSocket):
        """
        This function disconnects a user from a specified room in a Python async application.

        :param room_id: The `room_id` parameter is a unique identifier for the room from which the
        `websocket` connection needs to be disconnected. It is used to locate the specific room in the
        dictionary of rooms maintained by the server
        :type room_id: str
        :param websocket: The `websocket` parameter in the `disconnect_user` method is an instance of
        the WebSocket class representing the connection to a client. This parameter is used to identify
        and disconnect a specific user from a room identified by the `room_id`
        :type websocket: WebSocket
        """
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


# `room_manager = RoomManager()` is creating an instance of the `RoomManager` class and assigning it
# to the variable `room_manager`. This instance will be used to manage rooms, message queues, and
# broadcast tasks for handling WebSocket connections and message broadcasting within a chat service.
# The `RoomManager` instance will hold information about rooms, message queues, and tasks related to
# broadcasting messages to connected clients in real-time.
room_manager = RoomManager()


@chat_service.websocket("/message/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, room_id: str, token: str, db=Depends(get_db)
):
    """
    This function establishes a WebSocket connection, authenticates the user with a token, and
    manages message broadcasting within a specified room.

    :param websocket: The `websocket` parameter in the `websocket_endpoint` function represents the
    WebSocket connection object. It allows bidirectional communication between the server and the client
    in real-time. You can use this object to send and receive messages asynchronously over the WebSocket
    connection
    :type websocket: WebSocket
    :param room_id: The `room_id` parameter in the code snippet represents the identifier of the room to
    which the WebSocket connection is being established. This allows users to join specific rooms for
    real-time messaging or communication
    :type room_id: str
    :param token: The `token` parameter in the code snippet represents a token that is used to
    authenticate the user. It is passed as part of the WebSocket connection request to verify the
    identity of the user. The `get_user_from_token` function is likely responsible for validating this
    token and retrieving the corresponding user information from
    :type token: str
    :param db: The `db` parameter in the `websocket_endpoint` function is a dependency that is used to
    get the database connection within the FastAPI application. It is obtained using the `Depends`
    function with the `get_db` function as an argument. The `get_db` function likely returns the
    database
    """
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
    """
    This Python function retrieves information about all connections in chat rooms, including queue
    size, number of users connected, and user details.
    :return: A dictionary containing information about all the message rooms, including the queue size,
    number of users connected, and a list of users connected to each room.
    """
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
