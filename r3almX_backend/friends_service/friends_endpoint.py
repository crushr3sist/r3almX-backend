from fastapi import Depends

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.friends_service.main import friends_service


@friends_service.get("/get")
def get_friends(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
): ...


@friends_service.post("/request")
def make_friend(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
): ...
