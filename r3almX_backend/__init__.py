from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .version import __version__


class RealmX(FastAPI):
    def __init__(self, *, title: str = "r3almX", description: str = "r3almX API"):
        super().__init__(
            title=title,
            version=str(__version__),
            description=description,
            tags_metadata=[
                {"name": "Auth", "description": "Auth Endpoints"},
                {"name": "Chat", "description": "Chat Endpoints"},
                {"name": "Invite", "description": "Invite Endpoints"},
                {"name": "Room", "description": "Room Endpoints"},
                {"name": "Channel", "description": "Channel Endpoints"},
            ],
        )
        self.add_routes()
        self.configure_middleware()

    def configure_middleware(self):
        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*", "http://localhost:3000"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.add_middleware(SessionMiddleware, secret_key="feafawefawefawefawef")

    def add_routes(self):
        from r3almX_backend.auth_service.main import auth_router
        from r3almX_backend.chat_service.channel_system.main import channel_manager
        from r3almX_backend.chat_service.invite_system.main import invite_system
        from r3almX_backend.chat_service.room_service.main import rooms_service
        from r3almX_backend.realtime_service.main import realtime

        self.include_router(auth_router)
        self.include_router(realtime)

        self.include_router(rooms_service)
        self.include_router(invite_system)
        self.include_router(channel_manager)


r3almX = RealmX()
from .inst_modifiers import *

# from .proj_logger import *
