from fastapi import APIRouter

invite_system = APIRouter(prefix="/invite")

from .invite_system_endpoint import *
