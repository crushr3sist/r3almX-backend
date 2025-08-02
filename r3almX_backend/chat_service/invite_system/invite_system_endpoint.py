from fastapi import Depends, HTTPException

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.chat_service.invite_system.main import invite_system
from r3almX_backend.chat_service.models.rooms_model import RoomsModel

INVALID_ROOM_ID_MESSAGE = "Invalid room ID"
ROOM_NOT_FOUND_MESSAGE = "Room not found"
PERMISSION_DENIED_MESSAGE = "Permission denied"

"""
this is where the CRUD operations are handled for our invite system
"""


@invite_system.get("/get", tags=["Invite"])
async def get_invite(
    room_id: str, user: User = Depends(get_current_user), db=Depends(get_db)
):
    """
    Endpoint to get the invite link for a specific room.

    Parameters:
    - room_id (str): The ID of the room for which the invite link is requested.
    - user (User): The current user making the request.
    - db: The database session dependency.

    Returns:
    dict: A dictionary containing the status and the invite link if the room ID is valid.

    Raises:
    HTTPException: If the room ID is invalid (status code 404).
    """
    invite_link = (
        db.query(RoomsModel)
        .filter(RoomsModel.room_owner == user.id)
        .filter(RoomsModel.id == room_id)
        .first()
    )
    if not invite_link:
        raise HTTPException(status_code=404, detail=INVALID_ROOM_ID_MESSAGE)
    return {
        "status": 200,
        "invite_link": f"http://localhost:8000/invite/{invite_link.invite_key}",
    }


@invite_system.get("/{invite_key}", tags=["Invite"])
async def join(
    invite_key: str, user: User = Depends(get_current_user), db=Depends(get_db)
):
    room_query = (
        db.query(RoomsModel).filter(RoomsModel.invite_key == invite_key).first()
    )

    if room_query:
        if str(user.id) in room_query.members:
            print(room_query.members)
            return {
                "status": 302,
                "message": f"user {user.id} is already in room {room_query.room_name}",
            }
        else:
            (
                db.query(RoomsModel)
                .filter(RoomsModel.invite_key == invite_key)
                .update({RoomsModel.members: room_query.members + [user.id]})
            )

            (
                db.query(User)
                .filter(User.id == user.id)
                .update({User.rooms_joined: user.rooms_joined + [room_query.id]})
            )

            db.add(room_query)
            db.add(user)

            db.commit()

            db.refresh(room_query)
            db.refresh(user)

            return {
                "status": 200,
                "message": f"user {user.username} has joined {room_query.room_name} !!",
            }

    else:
        raise HTTPException(status_code=404, detail=ROOM_NOT_FOUND_MESSAGE)


@invite_system.put("/edit/invite", tags=["Invite"])
async def edit_invite(
    room_id: str, user: User = Depends(get_current_user), db=Depends(get_db)
):
    # generate a new invite key and modify the current record of the room id and assign the new invite link

    pass
