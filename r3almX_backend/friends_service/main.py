from fastapi import APIRouter

friends_service = APIRouter(prefix="/friends")

import r3almX_backend.friends_service.friends_endpoint
