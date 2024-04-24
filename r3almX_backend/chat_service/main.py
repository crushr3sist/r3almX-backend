from fastapi import APIRouter

chat_service = APIRouter(prefix="/chat")

from .chat_service_endpoints import *
