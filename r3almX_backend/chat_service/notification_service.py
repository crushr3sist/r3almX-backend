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
from r3almX_backend.chat_service.chat_service_endpoints import get_user_from_token
from r3almX_backend.chat_service.connection_service import connection_manager
from r3almX_backend.chat_service.main import chat_service


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


notification = NotificationSystem()


@chat_service.websocket("/notify")
async def notification_pusher(websocket: WebSocket, token: str, db=Depends(get_db)):
    # we need to manage a middleware so that if a user has associated events, we need to trigger the
    # notification system so we push notifs to that user
    # need to figure out how users would receive

    pass
