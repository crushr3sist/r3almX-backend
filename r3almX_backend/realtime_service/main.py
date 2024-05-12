from fastapi import APIRouter

realtime = APIRouter()

from .chat_service_endpoints import *
from .connection_service import *
from .notification_service import *
