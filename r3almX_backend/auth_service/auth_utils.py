from calendar import week
from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from google.auth.transport import requests
from google.oauth2 import id_token
from jose import JWTError, jwt
from pydantic import BaseModel

from r3almX_backend.auth_service import user_handler_utils
from r3almX_backend.auth_service.Config import UsersConfig

from .user_handler_utils import get_db, get_user_by_username, verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class TokenData(BaseModel):
    username: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"]


def create_access_token(
    data: dict,
) -> str:
    data_to_encode = data.copy()
    expire = datetime.now() + timedelta(weeks=2)
    data_to_encode.update({"exp": expire})
    return jwt.encode(
        data_to_encode, UsersConfig.SECRET_KEY, algorithm=UsersConfig.ALGORITHM
    )


def authenticate_user(
    username: str, password: str, google_token: str = None, db=Depends(get_db)
):
    user = get_user_by_username(db, username=username)
    if not user:
        return False
    if google_token:
        try:
            google_user = id_token.verify_oauth2_token(
                google_token, requests.Request(), UsersConfig.GOOGLE_CLIENT_ID
            )
            if user.google_id == google_user["sub"]:
                return user
        except ValueError:
            return False
    elif password and verify_password(password, user.hashed_password):
        return user
    return False


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: user_handler_utils.Session = Depends(user_handler_utils.get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        raise credentials_exception from e
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
