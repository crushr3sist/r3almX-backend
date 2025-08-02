from fastapi import APIRouter

rooms_service = APIRouter(prefix="/rooms")

from .room_management_endpoints import *
