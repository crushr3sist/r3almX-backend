import datetime
import uuid

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.chat_service.channel_system.channel_utils import (
    get_channel_model,
    get_message_model,
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


@channel_manager.get("/fetch", tags=["Channel"])
async def fetch_channels(
    room_id: str, user: User = Depends(get_current_user), db=Depends(get_db)
):
    try:
        _channel_query = get_channel_model(room_id)
        channels = db.query(_channel_query).all()
        return {"status": 200, "channels": channels}
    except Exception as e:
        return {"status": 401, "exception": HTTPException(401, e)}


@channel_manager.post("/message/insert", tags=["Channel"])
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


class MessageModel(BaseModel):
    id: uuid.UUID
    channel_id: uuid.UUID
    sender_id: uuid.UUID
    message: str
    timestamp: datetime.datetime


@channel_manager.get("/message/fetch", tags=["Channel"])
async def fetch_messages(
    channel_id: str,
    room_id: str,
    db=Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1),
    page_size: int = Query(20),
) -> list[MessageModel]:

    message_table = get_message_model(room_id)
    message_query = (
        db.query(message_table).filter(message_table.channel_id == channel_id).all()
    )  # replace this query with the redis cache instead
    start = (page - 1) * page_size
    end = start + page_size
    return message_query[start:end]


@channel_manager.post("/edit", tags=["Channel"])
async def edit_channel(
    room_name: str, user: User = Depends(get_current_user), db=Depends(get_db)
): ...


@channel_manager.post("/delete", tags=["Channel"])
async def delete_channel(
    room_name: str, user: User = Depends(get_current_user), db=Depends(get_db)
): ...
