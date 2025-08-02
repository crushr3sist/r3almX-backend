from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth")

from .auth_routes import *
