from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware


class RealmX(FastAPI):
    def __init__(self, *, title: str = "r3almX", description: str = "r3almX API"):
        super().__init__(
            title=title,
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
        from r3almX_backend.chat_service.models import channels_model, rooms_model
        from r3almX_backend.database import engine

        # rooms_model.Base.metadata.drop_all(bind=engine)
        # channels_model.Base.metadata.drop_all(bind=engine)
        # user_models.Base.metadata.drop_all(bind=engine)

        user_models.Base.metadata.create_all(bind=engine)
        # channels_model.Base.metadata.create_all(bind=engine)
        # rooms_model.Base.metadata.create_all(bind=engine)


r3almX = RealmX()
