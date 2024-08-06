from fastapi import Depends, Query
from sqlalchemy import func, select, text

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db, get_user_by_username
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.database import AsyncSession
from r3almX_backend.search_service.main import search_service


@search_service.get("/friends")
async def get_friends(
    query: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sql = text(
        """
        SELECT username, levenshtein(username, :query) AS distance
        FROM users
        WHERE levenshtein(username, :query) <= 5
        ORDER BY distance
        """
    )
    result = await db.execute(sql, {"query": query})
    user_found = result.fetchall()[0:5]

    results = [await get_user_by_username(db, username[0]) for username in user_found]
    return {
        "status": 200,
        "results": (
            {"id": user.id, "username": user.username, "pfp": user.profile_pic}
            for user in results
        ),
    }


@search_service.get("/tag")
def get_friends(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
    query: list[str] = Query(),
):
    # query hashtags and return post' ids
    ...
