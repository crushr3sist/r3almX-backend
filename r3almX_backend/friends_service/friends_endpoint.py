from fastapi import Depends, HTTPException
from sqlalchemy import func, select

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import (
    get_db,
    get_user,
    get_user_by_username,
)
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.database import AsyncSession
from r3almX_backend.friends_service.main import friends_service


@friends_service.get("/get")
async def get_friends(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    if len(user.friends) < 1:
        return {"friends": "no friends :("}
    try:
        limit_numb = 2
        if len(user.friends) <= 2:
            limit_numb = len(user.friends)

        friends_list = [
            {
                "user_id": friends.id,
                "username": friends.username,
                "pic": friends.profile_pic,
            }
            for friends in [
                await get_user(db, str(_)) for _ in user.friends[0:limit_numb]
            ]
        ]

        return {
            "status": 200,
            "friends": friends_list,
        }

    except IndexError as i:
        raise HTTPException(status_code=500, detail="You don't have enough friends")


@friends_service.post("/add")
async def make_friend(
    username: str,
    user_id: str | None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_to_add = await get_user_by_username(db, username)

    if user_id and str(user_to_add.id) != user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    are_friends = await db.execute(
        select(User).where(
            (User.id == user.id) & (User.friends.contains([user_to_add.id]))
        )
    )

    if (are_friends.first()) is not None:
        return {"status": 200, "friend_status": True, "message": "Already friends"}

    await db.execute(
        User.__table__.update()
        .where(User.id == user.id)
        .values(friends=func.array_append(User.friends, user_to_add.id))
    )

    await db.execute(
        User.__table__.update()
        .where(User.id == user_to_add.id)
        .values(friends=func.array_append(User.friends, user.id))
    )

    await db.commit()

    return {
        "status": 200,
        "friend_status": True,
        "message": "Friend added successfully",
    }


@friends_service.get("/status")
async def check_friend_status(user_id: str, user=Depends(get_current_user)):

    if user_id in [str(_) for _ in user.friends]:
        return {"friend_status": True}
    else:
        return {"friends_status": False}
