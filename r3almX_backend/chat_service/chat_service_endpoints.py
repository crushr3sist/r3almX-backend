from fastapi import Depends
from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.chat_service.main import chat_service
from r3almX_backend.chat_service.models import RoomsModel


""" 
this is where we connect users to channels
we need to write a **websocket handler** so multiple users
can poll messages in and out to certain channels

- write a feed websocket handler (client receiver)
- write a broadcast digest websocket handler (client  and message log updater)

"""
