from fastapi import Depends, Query

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.post_service.main import post_service
from r3almX_backend.post_service.post_model import PostModel
from r3almX_backend.post_service.types import Post, PostResponse


@post_service.get("/create")
async def create_post(
    new_post: Post,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):

    return new_post


@post_service.get("/feed")
async def aggregate_feed(
    new_post: PostResponse,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
): ...


@post_service.delete("/delete")
def delete_post(
    user: User = Depends(get_current_user), db=Depends(get_db), post_id: str = Query()
):
    # query hashtags and return post' ids
    ...
