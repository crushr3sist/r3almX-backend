from fastapi import FastAPI, Request, logger
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
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
        self.add_models()
        self.add_routes()
        self.configure_middleware()

    def configure_middleware(self):
        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
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

    def add_models(self):
        from r3almX_backend.auth_service import user_models
        from r3almX_backend.chat_service.models import rooms_model
        from r3almX_backend.database import engine

        # rooms_model.Base.metadata.drop_all(bind=engine)
        # channels_model.Base.metadata.drop_all(bind=engine)
        # user_models.Base.metadata.drop_all(bind=engine)

        user_models.Base.metadata.create_all(bind=engine)
        # channels_model.Base.metadata.create_all(bind=engine)
        # rooms_model.Base.metadata.create_all(bind=engine)


r3almX = RealmX()


@r3almX.middleware("http")
async def log_requests(request: Request, call_next):
    log_message = (
        f"IP Address: {request.client.host} | "
        f"User Agent: {request.headers.get('User-Agent')} | "
        f"Referrer: {request.headers.get('Referrer')} | "
        f"Request Method: {request.method} | "
        f"Request URL: {request.url}"
    )
    logger.info(log_message)

    response = await call_next(request)
    return response
