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
    """
    The function `create_access_token` generates a JWT access token with an expiration date two weeks from the current date.

    :param data: The `data` parameter is a dictionary containing the information that will be encoded into the access token. This information typically includes details about the user or client for whom the access token is being generated
    :type data: dict
    :return: The `create_access_token` function returns a tuple containing the encoded access token and the expiration date of the token.
    """
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
    """
    The `authenticate_user` function in Python checks user authentication based on email, password, and optional Google token.

    :param email: The `email` parameter in the `authenticate_user` function is a string that represents the email address of the user trying to authenticate
    :type email: str
    :param password: The `password` parameter in the `authenticate_user` function is a string that represents the password provided by the user for authentication
    :type password: str
    :param google_token: The `google_token` parameter in the `authenticate_user` function is used for authentication with Google. If a `google_token` is provided, the function will attempt to verify the token using Google's OAuth2 API. If the verification is successful and the Google user ID matches the user's Google ID
    :type google_token: str | None
    :param db: The `db` parameter in the `authenticate_user` function is a dependency that is used to get a database connection. It is obtained using the `Depends` function from the FastAPI framework. The `get_db` function is likely a helper function that provides access to the database connection within the
    :return: The `authenticate_user` function returns either the user object if authentication is successful, or `False` if authentication fails.
    """
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
    """
    The `get_current_user` function validates a JWT token, decodes it to extract the email, and retrieves the user from the database based on the email.

    :param token: The `token` parameter is used to authenticate the user. It is obtained from the request headers and is expected to be in a specific format. In this case, it is validated using an OAuth2 scheme. If the token is valid, it is decoded to extract the user's email address for further
    :type token: str
    :param db: The `db` parameter in the `get_current_user` function is an instance of an asynchronous database session. It is obtained using the `get_db` dependency, which likely sets up a connection to the database for interacting with user data. This parameter is used within the function to query the database and
    :type db: AsyncSession
    :return: The `get_current_user` function is returning the user object retrieved from the database based on the email extracted from the JWT token. If the token is invalid or the user does not exist in the database, it raises a `HTTPException` with a status code of 401 (UNAUTHORIZED) and the detail message "Could not validate credentials".
    """
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
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as e:
        raise credentials_exception from e
    user = await get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user
