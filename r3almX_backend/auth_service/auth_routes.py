import json
import secrets
from datetime import datetime, timedelta

import httpx
import requests
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError, jwt

from r3almX_backend.auth_service import user_handler_utils
from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_schemas import UserCreate

from .auth_utils import authenticate_user, create_access_token, get_current_user
from .Config import UsersConfig
from .main import auth_router
from .user_models import AuthData, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

import urllib.parse
from io import BytesIO

import pyotp


@auth_router.post("/google/callback")
async def auth_google_callback(request: Request, db=Depends(user_handler_utils.get_db)):
    try:
        data = await request.json()  # Parse the JSON payload from the request
        code = data.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")

        # Verify the ID token
        google_user_info = google_id_token.verify_oauth2_token(
            code, google_requests.Request(), UsersConfig.GOOGLE_CLIENT_ID
        )
        email = google_user_info.get("email")
        print(email)

        if not email:
            raise HTTPException(status_code=400, detail="Email not found in token")

        # Check if the user exists, if not, create a new user
        if not user_handler_utils.get_user_by_email(db, email):
            user = user_handler_utils.create_user(
                db,
                UserCreate(
                    username=email,
                    email=email,
                    password=secrets.token_urlsafe(32),
                ),
            )
            # Create a new access token for the user
            user_access_token = create_access_token(data={"sub": user.username})
            print(user_access_token)
            return {"access_token": user_access_token, "token_type": "bearer"}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Google login failed: {str(e)}")


@auth_router.post("/register", tags=["Auth"])
def create_user(
    user: user_handler_utils.user_schemas.UserCreate = Depends(),
    db: user_handler_utils.Session = Depends(user_handler_utils.get_db),
):

    if db_user := user_handler_utils.get_user_by_username(db, username=user.username):
        return {
            "status_code": 400,
            "detail": "User with this email already exists",
            "user": db_user,
        }

    try:
        db_user = user_handler_utils.create_user(db=db, user=user)
        otp_secret_key = pyotp.random_base32()
        user_handler_utils.create_auth_data(
            db=db, user_id=db_user.id, otp_secret_key=otp_secret_key
        )

        return {"status_code": 200, "detail": "User created successfully"}
    except Exception as e:
        return {"status_code": 400, "detail": str(e)}


@auth_router.post("/token", tags=["Auth"])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    google_token: str = None,
    db=Depends(user_handler_utils.get_db),
):

    user = authenticate_user(
        username=form_data.username,
        password=form_data.password,
        google_token=google_token,
        db=db,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username},
        expire_delta=timedelta(weeks=1),
    )
    user_handler_utils.set_user_online(db, user.id)

    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/token/check", tags=["Auth"])
def verify_token(token: str):
    try:
        token_data = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )

    except JWTError as j:
        return {"status": 401, "is_user_logged_in": False}

    return {"status": "200", "is_user_logged_in": True}


@auth_router.post("/token/refresh", tags=["Auth"])
def login_for_access_token(
    db=Depends(user_handler_utils.get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": current_user.username}, expire_delta=timedelta(weeks=1)
        )

    except Exception as e:
        return {"error": e, "status": 500}

    return {"access_token": access_token, "token_type": "bearer", "status": 200}
