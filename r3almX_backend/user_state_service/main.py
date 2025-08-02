from fastapi import APIRouter

state_service = APIRouter(prefix="/user_state")

from .user_state_routes import *
