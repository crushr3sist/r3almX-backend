from fastapi import APIRouter

post_service = APIRouter(prefix="/post")

import r3almX_backend.post_service.post_endpoints
