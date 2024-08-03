from uuid import uuid4

from fastapi import Depends, HTTPException
from sqlalchemy.event import listen
from sqlalchemy import select

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.chat_service.channel_system.channel_utils import get_channel_model
from r3almX_backend.chat_service.models.rooms_model import RoomsModel
from r3almX_backend.chat_service.models.rooms_table import (
    create_channel_table,
    create_message_table,
)
from r3almX_backend.chat_service.room_service.main import rooms_service
from r3almX_backend.database import SessionLocal, engine, Base

INVALID_ROOM_ID_MESSAGE = "Invalid room ID"
ROOM_NOT_FOUND_MESSAGE = "Room not found"
PERMISSION_DENIED_MESSAGE = "Permission denied"


@rooms_service.post("/create", tags=["Room"])
async def create_room_endpoint(
    room_name: str, user: User = Depends(get_current_user), db=Depends(get_db)
):
    new_room = RoomsModel(str(user.id) , room_name)
    new_room.members = [str(user.id)]

    db.add(new_room)
    await db.commit()
    await db.refresh(new_room)

    channel_table = create_channel_table(new_room.id)
    message_table = create_message_table(new_room.id)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Update the user's rooms_joined
    user.rooms_joined = user.rooms_joined + [str(new_room.id)]
    await db.commit()

    return {"status": 200, "rooms": new_room, "user": user}


@rooms_service.post("/ban", tags=["Room"])
async def ban_user(
    room_id: str, user: User = Depends(get_current_user), db=Depends(get_db)
): ...


@rooms_service.post("/kick", tags=["Room"])
async def kick_user(
    room_id: str, user: User = Depends(get_current_user), db=Depends(get_db)
): ...


@rooms_service.get("/fetch", tags=["Room"])
async def fetch_rooms(user: User = Depends(get_current_user), db=Depends(get_db)):
    rooms = []
    try:
        for users_rooms in set(user.rooms_joined):
            rooms_query = await (
                db.execute(select(RoomsModel).filter(RoomsModel.id == users_rooms))

            )
            _rooms_query = rooms_query.scalars().all()
            rooms.append(_rooms_query[0])

    except Exception as e:
        return {"status": 400, "error": str(e)}
    return {"status": 200, "rooms": rooms}


@rooms_service.put("/edit", tags=["Room"])
async def edit_room(
    room_id: str,
    new_name: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    room_to_update = (
        db.query(RoomsModel)
        .filter(RoomsModel.room_owner == user.id)
        .filter(RoomsModel.id == room_id)
        .first()
    )

    if room_to_update:
        room_to_update.room_name = new_name
        db.commit()

        return {"status": "room updated successfully", "update": room_to_update}


@rooms_service.delete("/delete", tags=["Room"])
async def create_room(
    room_id: str, user: User = Depends(get_current_user), db=Depends(get_db)
):
    room_to_delete = (
        db.query(RoomsModel)
        .filter(RoomsModel.room_owner == user.id)
        .filter(RoomsModel.id == room_id)
        .first()
    )

    if room_to_delete:
        db.delete(room_to_delete)
        db.commit()
        return {"status": 200}
    else:
        raise HTTPException(status_code=404, detail=PERMISSION_DENIED_MESSAGE)
