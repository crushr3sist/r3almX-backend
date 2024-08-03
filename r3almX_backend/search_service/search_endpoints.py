from fastapi import Depends, Query

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.search_service.main import search_service


@search_service.get("/friends")
def get_friends(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
    friends_query: str = Query(),
):
    # query usernames and handles and return user id
    ...


@search_service.get("/tag")
def get_friends(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
    query: list[str] = Query(),
):
    # query hashtags and return post' ids
    ...
