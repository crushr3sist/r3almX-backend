from fastapi import APIRouter

channel_manager = APIRouter(prefix="/channel")

from .channel_management_endpoints import *
