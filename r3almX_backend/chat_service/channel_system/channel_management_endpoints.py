import uuid

from fastapi import Depends, HTTPException
from sqlalchemy import Table, insert, select

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.chat_service.channel_system.channel_utils import (
    insert_to_channels_table,
    insert_to_messages_table,
)
from r3almX_backend.chat_service.channel_system.main import channel_manager
from r3almX_backend.chat_service.models.channels_model import ChannelsModel
from r3almX_backend.chat_service.models.rooms_model import RoomsModel
from r3almX_backend.database import *


@channel_manager.post("/create", tags=["Channel"])
async def create_channel(
    channel_description: str,
    channel_name: str,
    room_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):

    try:
        insert_to_channels_table(
            room_id,
            db,
            user,
            channel_name=channel_name,
            channel_description=channel_description,
        )
        return {"message": "Channel created successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating channel: {str(e)}")


@channel_manager.post("/insert", tags=["Channel"])
async def create_channel(
    channel_id: str,
    message: str,
    room_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):

    try:
        insert_to_messages_table(
            room_id=room_id,
            db=db,
            user=user,
            message=message,
            channel_id=channel_id,
        )
        return {"message": "message committed."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating channel: {str(e)}")


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
