from fastapi import Depends

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.chat_service.channel_system.main import channel_manager
from r3almX_backend.chat_service.models.channels_model import ChannelsModel
from r3almX_backend.chat_service.models.rooms_model import RoomsModel


@channel_manager.post("/create", tags=["Channel"])
async def create_channel(
    channel_description: str,
    channel_name: str,
    room_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    room = db.query(RoomsModel).filter(RoomsModel.id == room_id).first()
    if room:

        new_room = ChannelsModel(
            channel_name=channel_name,
            channel_description=channel_description,
            room_id=room.id,
            author=user.id,
        )

        db.add(new_room)
        db.commit()
        db.refresh(new_room)


@channel_manager.post("/quick_digest", tags=["Channel"])
async def quick_digest(
    room_name: str, user: User = Depends(get_current_user), db=Depends(get_db)
): ...


@channel_manager.post("/mass_digest", tags=["Channel"])
async def mass_digest(
    room_name: str, user: User = Depends(get_current_user), db=Depends(get_db)
): ...


@channel_manager.post("/edit", tags=["Channel"])
async def edit_channel(
    room_name: str, user: User = Depends(get_current_user), db=Depends(get_db)
): ...


@channel_manager.post("/delete", tags=["Channel"])
async def delete_channel(
    room_name: str, user: User = Depends(get_current_user), db=Depends(get_db)
): ...
