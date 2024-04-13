from datetime import datetime, timedelta
from typing import Literal
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service import user_handler_utils
from .user_handler_utils import get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class TokenData(BaseModel):
    username: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"]


def create_access_token(
    data: dict,
    expire_delta: Optional[timedelta] = UsersConfig.ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    data_to_encode = data.copy()
    if expire_delta:
        expire = datetime.utcnow() + expire_delta
        data_to_encode.update({"exp": expire})
    return jwt.encode(
        data_to_encode, UsersConfig.SECRET_KEY, algorithm=UsersConfig.ALGORITHM
    )


def create_access_token(
    data: dict, expire_delta: Optional[int] = UsersConfig.ACCESS_TOKEN_EXPIRE_MINUTES
) -> str:
    data_to_encode = data.copy()
    if expire_delta:
        expire = datetime.utcnow() + expire_delta
        data_to_encode.update({"exp": expire})
    return jwt.encode(
        data_to_encode, UsersConfig.SECRET_KEY, algorithm=UsersConfig.ALGORITHM
    )


def authenticate_user(
    username: str,
    password: str,
    db: user_handler_utils.Session = Depends(user_handler_utils.get_db),
):
    if user := get_user_by_username(db, username=username):
        return (
            user
            if user_handler_utils.verify_password(password, user.hashed_password)
            else False
        )
    else:
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
