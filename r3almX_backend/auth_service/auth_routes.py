import secrets
from datetime import timedelta

import pyotp
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_handler_utils import (
    create_auth_data,
    create_user_record,
    get_db,
    get_user_by_email,
    get_user_by_username,
    set_user_online,
)
from r3almX_backend.auth_service.user_schemas import UserCreate

from .auth_utils import authenticate_user, create_access_token, get_current_user
from .Config import UsersConfig
from .main import auth_router
from .user_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@auth_router.post("/google/callback", tags=["Auth"])
async def auth_google_callback(request: Request, db=Depends(get_db)):
    try:
        data = await request.json()
        code = data.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")

        google_user_info = google_id_token.verify_oauth2_token(
            code,
            google_requests.Request(),
            UsersConfig.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=30 * 60,
        )
        print(google_user_info)
        if not google_user_info:
            raise HTTPException(status_code=500, detail="Email could not be verified")

        email = google_user_info.get("email")
        print(email)
        if not email:
            raise HTTPException(status_code=400, detail="Email not found in token")

        if not (await get_user_by_email(db, email)):
            print("user doesn't exist")
            try:
                print("trying to create a user")
                validated_info = UserCreate(
                    username=email,
                    email=email,
                    password=secrets.token_urlsafe(32),
                    google_id=google_user_info.get("sub"),
                    profile_pic=google_user_info.get("picture"),
                )
                print(validated_info)
                await create_user_record(db, validated_info)
            except Exception as e:
                return HTTPException(status_code=500, detail=e)
        user = await get_user_by_email(db, email)
        print(user.username)
        print(user.email)

        username_set = True
        if user.email == user.username:
            username_set = False

        user_access_token = create_access_token(data={"sub": str(user.email)})
        print(user_access_token)

        return {
            "access_token": user_access_token,
            "token_type": "bearer",
            "username_set": username_set,
        }

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Google login failed: {str(e)}")


@auth_router.patch("/change_username", tags=["Auth"])
async def assign_username(
    username: str,
    token: str,
    db=Depends(get_db),
):
    payload = jwt.decode(
        token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
    )
    email: str = payload.get("sub")
    user_inst = await get_user_by_email(db, email)
    user_inst.username = str(username)
    access_token = create_access_token(
        data={"sub": user_inst.email},
    )

    await db.commit()

    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/fetch", tags=["Auth"])
async def verify_token(token: str, db=Depends(get_db)):
    try:
        decoded_token = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )

        user = await get_user_by_email(db, decoded_token.get("sub"))
        if user:
            return {
                "status": 200,
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "pic": user.profile_pic,
                },
            }
        return {"status": 401, "is_user_logged_in": False}

    except JWTError as j:
        return {"status": 401, "is_user_logged_in": False}


@auth_router.get("/token/check", tags=["Auth"])
async def verify_token(token: str, db=Depends(get_db)):
    try:
        decoded_token = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )

        print({**decoded_token})

        user = await get_user_by_email(db, decoded_token.get("sub"))
        if user:
            return {
                "status": 200,
                "is_user_logged_in": True,
                "user": [user.id, user.username, user.email],
            }
        return {"status": 401, "is_user_logged_in": False}

    except JWTError as j:
        return {"status": 401, "is_user_logged_in": False}


@auth_router.post("/token", tags=["Auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    google_token: str = None,
    db=Depends(get_db),
):

    user = await authenticate_user(
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
    set_user_online(db, user.id)

    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/token/refresh", tags=["Auth"])
async def login_for_access_token(
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        access_token = create_access_token(
            data={"sub": current_user.username}, expire_delta=timedelta(weeks=1)
        )

    except Exception as e:
        return {"error": e, "status": 500}

    return {"access_token": access_token, "token_type": "bearer", "status": 200}


@auth_router.post("/register", tags=["Auth"])
async def create_user(
    user: UserCreate = Depends(),
    db: AsyncSession = Depends(get_db),
):

    if db_user := await get_user_by_username(db, username=user.username):
        return {
            "status_code": 400,
            "detail": "User with this email already exists",
            "user": db_user,
        }

    try:
        db_user = await create_user(db=db, user=user)
        otp_secret_key = pyotp.random_base32()
        create_auth_data(db=db, user_id=db_user.id, otp_secret_key=otp_secret_key)

        return {"status_code": 200, "detail": "User created successfully"}
    except Exception as e:
        return {"status_code": 400, "detail": str(e)}
