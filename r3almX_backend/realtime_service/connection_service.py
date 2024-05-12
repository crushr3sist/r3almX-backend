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
from r3almX_backend.realtime_service.chat_service import get_user_from_token
from r3almX_backend.realtime_service.main import realtime


class Connection:
    def __init__(self):
        # use redis to cache users connected

        # connection cache status contains {user_id, status}
        self.connection_status_cache: Dict[str, str] = self.get_status_cache()

        # connection cache sockets contain {user_id, websocket}
        self.connection_sockets: Dict[str, WebSocket] = {}

    def connect(self):
        # we add the user to the connection array
        # but we implement a heartbeat so our server doesn't keep users in memory that aren't connected
        ...

    def disconnect(self):
        # remove the user from the heartbeat pool
        ...

    def get_status_cache(self) -> Dict[str, str]:
        # we get cache from redis and construct it into dict and return it
        ...

    def set_online(self):
        # class A: we're gonna push users notifications
        pass

    def set_offline(self):
        # class B: mobile notif push (web:toast, mobile: notif)
        pass

    def set_dnd(self):
        # class C: integer notif push (silent number increment)
        pass

    def is_connected(self, user_id) -> bool:
        try:
            if self.connection_status_cache.get(
                f"{user_id}"
            ) or self.connection_sockets.get(f"{user_id}"):
                return True
            return False
        except KeyError as k:
            return False

    def get_status(self, user_id) -> str:
        return self.connection_cache_status.get(f"{user_id}")

    def set_status(self, user_id, status):
        # this is the function exposed to the websocket
        # so we can update the status
        # we also call set_status_cache
        ...

    def set_status_cache(self, user_id, status):
        # modifies the redis cache status of the user
        ...


connection_manager = Connection()


@realtime.websocket("/feedback")
async def feedback(websocket: WebSocket, token: str, db=Depends(get_db)):
    # simple websocket endpoint to receive feedback from the client so we know what users to keep in heartbeat pool
    # automatic disconnect only, we have a connection websocket to connect to

    ...


@realtime.websocket("/connect")
async def connect(websocket: WebSocket, token: str, db=Depends(get_db)):
    # write a wholistic solution for connection so that we can send notif
    user = get_user_from_token(token)
    if user:
        await websocket.accept()
        while True:
            # check the status of the user.
            # if they're not in the connection sockets, then just connect them
            # otherwise we need to check their last set status from the cache
            # we need to also check the websocket request
            # it should contain json with user id and requested change in connection
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
    else:
        return websocket.close(1001)
