from uuid import uuid4

from fastapi import Depends, HTTPException
from sqlalchemy.event import listen

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.chat_service.models.rooms_model import RoomsModel
from r3almX_backend.chat_service.models.rooms_table import (
    create_channel_table,
    create_message_table,
)
from r3almX_backend.chat_service.room_service.main import rooms_service
from r3almX_backend.database import engine

INVALID_ROOM_ID_MESSAGE = "Invalid room ID"
ROOM_NOT_FOUND_MESSAGE = "Room not found"
PERMISSION_DENIED_MESSAGE = "Permission denied"


@rooms_service.post("/create", tags=["Room"])
async def create_room(
    room_name: str, user: User = Depends(get_current_user), db=Depends(get_db)
):
    new_room = RoomsModel(user.id, room_name)

    (
        db.query(RoomsModel)
        .filter(RoomsModel.room_owner == user.id)
        .update({RoomsModel.members: new_room.members + [user.id]})
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    channel_table = create_channel_table(new_room.id)
    message_table = create_message_table(new_room.id)

    channel_table.create(engine, checkfirst=True)
    message_table.create(engine, checkfirst=True)

    (
        db.query(User)
        .filter(User.id == user.id)
        .update({User.rooms_joined: user.rooms_joined + [new_room.id]})
    )

    db.add(user)
    db.commit()

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
            rooms_query = (
                db.query(RoomsModel).filter(RoomsModel.id == users_rooms).all()
            )
            rooms.append(rooms_query)
    except Exception as e:
        return {"status": 400, "rooms": "User is not in any rooms"}

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
