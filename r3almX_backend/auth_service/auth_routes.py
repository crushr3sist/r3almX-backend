import secrets
from datetime import timedelta

import pyotp
from fastapi import Depends, HTTPException, Request, status
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
from .user_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@auth_router.post("/google/callback", tags=["Auth"])
async def auth_google_callback(request: Request, db=Depends(user_handler_utils.get_db)):
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
        print(str(google_user_info))
        if not google_user_info:
            raise HTTPException(status_code=500, detail="Email could not be verified")

        email = google_user_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email not found in token")

        if not (user_handler_utils.get_user_by_email(db, email)):
            print("user doesn't exist")
            try:
                user_handler_utils.create_user(
                    db,
                    UserCreate(
                        username=email,
                        email=email,
                        password=secrets.token_urlsafe(32),
                        google_id=google_user_info.get("sub"),
                        profile_pic=google_user_info.get("picture"),
                    ),
                )
            except Exception as e:
                return HTTPException(status_code=500, detail=e)
        user = user_handler_utils.get_user_by_email(db, email)

        username_set = True
        if user.email == user.username:
            username_set = False

        user_access_token = create_access_token(data={"sub": str(user.email)})

        return {
            "access_token": user_access_token,
            "token_type": "bearer",
            "username_set": username_set,
        }

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Google login failed: {str(e)}")


@auth_router.patch("/change_username", tags=["Auth"])
def assign_username(
    username: str,
    token: str,
    db=Depends(user_handler_utils.get_db),
):
    payload = jwt.decode(
        token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
    )

    email: str = payload.get("sub")
    print(email)
    user_inst = user_handler_utils.get_user_by_email(db, email)
    print(user_inst.id)
    user_inst.username = str(username)

    access_token = create_access_token(
        data={"sub": user_inst.email},
    )

    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/fetch", tags=["Auth"])
def verify_token(token: str, db=Depends(user_handler_utils.get_db)):
    try:
        decoded_token = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )

        user = user_handler_utils.get_user_by_email(db, decoded_token.get("sub"))
        if user:
            return {
                "status": 200,
                "user": {"username": user.username, "email": user.email},
            }
        return {"status": 401, "is_user_logged_in": False}

    except JWTError as j:
        return {"status": 401, "is_user_logged_in": False}


@auth_router.get("/token/check", tags=["Auth"])
def verify_token(token: str, db=Depends(user_handler_utils.get_db)):
    try:
        decoded_token = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )

        print({**decoded_token})

        user = user_handler_utils.get_user_by_email(db, decoded_token.get("sub"))
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


@auth_router.post("/token/refresh", tags=["Auth"])
def login_for_access_token(
    db=Depends(user_handler_utils.get_db),
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
