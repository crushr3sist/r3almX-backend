from fastapi import APIRouter

realtime = APIRouter()

from .chat_service import *  # noqa: E402, F403
from .connection_service import *  # noqa: E402, F403
from .observer_service import *  # noqa: E402, F403
