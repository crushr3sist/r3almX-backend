import secrets

import pyotp
from fastapi import Body, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError, jwt

from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_handler_utils import (
    create_auth_data,
    create_user_record,
    get_db,
    get_user_by_email,
    get_user_by_username,
    verify_password,
)
from r3almX_backend.auth_service.user_schemas import UserCreate

from .auth_utils import create_access_token, get_current_user
from .main import auth_router
from .user_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_token_from_header(request: Request):
    token = request.headers.get("Authorization")
    if token is None or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return token.split(" ")[1]


@auth_router.post("/google/callback", tags=["Auth"])
async def auth_google_callback(request: Request, db=Depends(get_db)):
    try:
        data: dict = await request.json()
        print(data)
        code = data.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")

        google_user_info: dict = google_id_token.verify_oauth2_token(
            code,
            google_requests.Request(),
            UsersConfig.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=30 * 60,
        )
        if not google_user_info:
            raise HTTPException(status_code=500, detail="Email could not be verified")

        email = google_user_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email not found in token")
        if not (await get_user_by_email(db, email)):
            try:
                validated_info = UserCreate(
                    username=email,
                    email=email,
                    password=secrets.token_urlsafe(32),
                    google_id=google_user_info.get("sub"),
                    profile_pic=google_user_info.get("picture"),
                )
                await create_user_record(db, validated_info)
            except Exception as e:
                return HTTPException(status_code=500, detail=e)
        user = await get_user_by_email(db, email)

        username_set = True
        if user.email == user.username:
            username_set = False
        user_access_token, expire_time = create_access_token(
            data={"sub": str(user.email)}
        )

        return {
            "access_token": user_access_token,
            "token_type": "bearer",
            "expire_time": expire_time,
            "username_set": username_set,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google login failed: {str(e)}")


@auth_router.post("/login", tags=["Auth"])
async def login_user(
    email: str | None, username: str | None, password: str | None, db=Depends(get_db)
):
    """
    check if either of the fields are empty, return 401
    check if user exists by email -> password
    if username given: username -> password

    if checks are correct:
        jwt token is issued and returned to the client
    """

    if username is None or email is None or password is None:
        return {"status_code": 401, "message": "log in data - missing fields"}
    try:

        if (queried_user := await get_user_by_email(db, email)) or (
            queried_user := await get_user_by_username(username)
        ):
            if password and await verify_password(
                password, queried_user.hashed_password
            ):
                access_token, expire_time = create_access_token(
                    data={"sub": str(email)}
                )

                {
                    "status_code": 200,
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expire_time": expire_time,
                }
    except Exception as e:
        return {"status_code": 500, "message": f"there was an error\n{e}"}


@auth_router.post("/register", tags=["Auth"])
async def create_user(
    user: UserCreate = Body(...),
    db=Depends(get_db),
):

    db_user = await get_user_by_username(db, username=user.username)
    if db_user:
        return {
            "status_code": 400,
            "detail": "User with this email already exists",
            "user": db_user,
        }

    try:
        db_user = await create_user_record(db=db, user=user)
        otp_secret_key = pyotp.random_base32()
        await create_auth_data(
            db=db, user_id=str(db_user.id), otp_secret_key=otp_secret_key
        )

        return {"status_code": 200, "detail": "User created successfully"}
    except Exception as e:
        return {"status_code": 400, "detail": str(e)}


@auth_router.post("/change_username", tags=["Auth"])
async def assign_username(
    username: str,
    token: str = Depends(get_token_from_header),
    db=Depends(get_db),
):
    payload = jwt.decode(
        token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
    )
    email: str = payload.get("sub")
    if email is None:
        return HTTPException(404, "email was null")
    user_inst = await get_user_by_email(db, email)
    user_inst.username = str(username)

    await db.commit()

    return {
        "status_code": 200,
        "message": "name changed successfully",
    }


@auth_router.get("/fetch", tags=["Auth"])
async def verify_token(token: str = Depends(get_token_from_header), db=Depends(get_db)):
    try:
        decoded_token = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )

        email = decoded_token.get("sub")
        if not isinstance(email, str):
            raise HTTPException(status_code=400, detail="Invalid token payload")
        user = await get_user_by_email(db, email)
        if user:
            return {
                "status_code": 200,
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "pic": user.profile_pic,
                },
            }
        return {"status_code": 401, "is_user_logged_in": False}

    except JWTError:
        return {"status_code": 401, "is_user_logged_in": False}


@auth_router.get("/fetch/user", tags=["Auth"])
async def verify_user_token(
    username: str, token: str = Depends(get_token_from_header), db=Depends(get_db)
):
    try:
        jwt.decode(token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM])

        user = await get_user_by_username(db, username)
        if user:
            return {
                "status_code": 200,
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "pic": user.profile_pic,
                },
                "is_user_logged_in": True,
            }
        return {"status_code": 401, "is_user_logged_in": False}

    except JWTError:
        return {"status_code": 401, "is_user_logged_in": False}


@auth_router.get("/token/verify", tags=["Auth"])
async def token_verify(token: str = Depends(get_token_from_header), db=Depends(get_db)):
    """
    requirements for valid token:
    - must be decodable by the backend
    - must contain a valid user within token
    - must not be expired
    """

    if token == "null" or token is None:
        return {"status_code": 401, "is_user_logged_in": False}
    try:
        decoded_token = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )

        user = await get_user_by_email(db, str(decoded_token.get("sub")))
        if user:
            return {
                "status_code": 200,
                "is_user_logged_in": True,
                "user": [user.id, user.username, user.email],
            }
        return {"status_code": 401, "is_user_logged_in": False}

    except JWTError:
        return {"status_code": 401, "is_user_logged_in": False}


@auth_router.post("/token/refresh", tags=["Auth"])
async def token_refresh(
    current_user: User = Depends(get_current_user),
):
    try:
        access_token = create_access_token(data={"sub": current_user.username})

    except Exception as e:
        return {"error": e, "status_code": 500}

    return {"access_token": access_token, "token_type": "bearer", "status_code": 200}
