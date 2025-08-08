from datetime import datetime, timedelta
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from google.auth.transport import requests
from google.oauth2 import id_token
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_handler_utils import (
    get_db,
    get_user_by_email,
    verify_password,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class TokenData(BaseModel):
    email: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"]


def create_access_token(
    data: dict,
):
    data_to_encode = data.copy()
    expire = datetime.now() + timedelta(weeks=2)
    data_to_encode.update({"exp": expire})
    return (
        jwt.encode(
            data_to_encode, UsersConfig.SECRET_KEY, algorithm=UsersConfig.ALGORITHM
        ),
        expire,
    )


async def authenticate_user(
    email: str,
    password: str,
    google_token: str | None = None,
    db=Depends(get_db),
):
    user = await get_user_by_email(db, email=email)
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
    elif password and await verify_password(password, user.hashed_password):
        return user
    return False


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:

        if not token or "." not in token:
            print(f"Invalid token format: {token}")
            raise credentials_exception

        payload = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            print("exception as called here: LINE 90", e)
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as e:
        print("exception as called here: LINE 94", e)
        raise credentials_exception from e
    user = await get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user
