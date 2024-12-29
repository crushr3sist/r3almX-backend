import datetime
import time
import uuid

import redis
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

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


class MessageModel(BaseModel):
    id: uuid.UUID
    channel_id: uuid.UUID
    sender_id: uuid.UUID
    message: str
    timestamp: datetime.datetime


@channel_manager.post("/create", tags=["Channel"])
async def create_channel(
    channel_description: str,
    channel_name: str,
    room_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    try:
        await insert_to_channels_table(
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
    room_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        _channel_query = get_channel_model(room_id)
        channels = await db.execute(select(_channel_query))

        return {"status": 200, "channels": channels.scalars().all()}
    except Exception as e:
        return {"status": 401, "exception": HTTPException(401, e)}


@channel_manager.post("/message/insert", tags=["Channel"])
async def insert_message(
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


@channel_manager.post("/edit", tags=["Channel"])
async def edit_channel(
    room_name: str, user: User = Depends(get_current_user), db=Depends(get_db)
): ...


@channel_manager.delete("/delete", tags=["Channel"])
async def delete_channel(
    channel_id, room_id, user: User = Depends(get_current_user), db=Depends(get_db)
):
    temp_redis = redis.Redis().from_url(
        url="redis://172.22.96.1:6379", decode_responses=True, db=1
    )
    try:
        # Get the models for channel and message based on room_id
        channel_query = get_channel_model(room_id)
        message_table = get_message_model(room_id)

        # Delete all messages associated with the channel
        messages = delete(message_table).where(message_table.channel_id == channel_id)
        channels = delete(channel_query).where(channel_query.id == channel_id)
        await db.execute(messages)
        await db.execute(channels)

        # Commit the transaction to finalize the changes
        await db.commit()
    except Exception as e:
        # Roll back the transaction in case of an exception
        await db.rollback()
        # Handle the exception (e.g., by logging or re-raising)
        time.sleep(1)
        print(e, "\n")

        raise HTTPException(
            status_code=500, detail="Failed to delete channel and its messages."
        ) from e
    try:
        # remove the cache entry
        temp_redis.delete(f"room:{room_id}:channel:{channel_id}:messages")
    except Exception as e:
        print(e, "\n")
        raise HTTPException(status_code=500, detail="Failed to remove cache.") from e
    temp_redis.close()
    return {"message": "Channel and its messages deleted successfully."}


@channel_manager.delete("/delete/message", tags=["Channel"])
async def delete_message(
    room_id, message_id, user: User = Depends(get_current_user), db=Depends(get_db)
):
    message_table = get_message_model(room_id)
    db.query(message_table).filter(message_table.id == message_id).delete()
    db.commit()

    return {"message": f"message-{message_id} deleted"}
