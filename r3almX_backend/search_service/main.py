from fastapi import APIRouter

search_service = APIRouter(prefix="/search")

import r3almX_backend.search_service.search_endpoints
