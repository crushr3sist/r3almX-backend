from fastapi import Depends

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db, get_user_by_username
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.database import AsyncSession
from r3almX_backend.friends_service.main import friends_service


@friends_service.get("/get")
def get_friends(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
): ...


@friends_service.post("/add")
async def make_friend(
    username: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    user_to_add = await get_user_by_username(db, username)
    await db.begin()
    user.friends = [user.friends].append(user_to_add.id)
    user_to_add.friends = [user_to_add.friends].append(user.id)
    await db.commit()

    return 200
