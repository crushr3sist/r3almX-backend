import secrets

import pyotp
from fastapi import Body, Depends, HTTPException, Query, Request, status
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
    """
    The function `auth_google_callback` handles the Google OAuth callback, verifies the user's email, creates a new user record if necessary, and generates an access token for the user.

    :param request: The `request` parameter in the `auth_google_callback` function represents the incoming HTTP request made to the endpoint `/google/callback`. It allows you to access data sent in the request, such as query parameters, headers, and the request body. In this case, the function is expecting a JSON payload
    :type request: Request
    :param db: The `db` parameter in the code snippet represents the database connection or session. It is used to interact with the database to perform operations like querying, creating, or updating records. In this case, it is being passed as a dependency to the `auth_google_callback` route to access the database within
    :return: The code snippet is a FastAPI endpoint for handling Google OAuth callback. It verifies the authorization code received from the client, validates the Google user information, and creates a new user record if the user does not exist in the database. Finally, it generates an access token for the user and returns a JSON response containing the access token, token type, expiration time, and a flag indicating whether the username is
    """

    try:
        data: dict = await request.json()
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
        print(user)
        username_set = True
        if user.email == user.username:
            username_set = False
        print(str(user.email))
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
        print(e)
        raise HTTPException(status_code=500, detail=f"Google login failed: {str(e)}")


@auth_router.post("/register", tags=["Auth"])
async def create_user(
    user: UserCreate = Body(...),
    db=Depends(get_db),
):
    """
    This function creates a new user in the database with error handling for existing users.

    :param user: The `user` parameter in the `create_user` function represents the data of a user that is being created. It is of type `UserCreate`, which likely contains information such as the user's username, password, email, etc. This data is provided in the request body when a new user
    :type user: UserCreate
    :param db: The `db` parameter in the `create_user` function is a dependency that is used to get a database connection. It is obtained using the `Depends` function from FastAPI. The `get_db` function is likely defined elsewhere in the codebase and is responsible for providing a database session
    :return: The code snippet is a FastAPI endpoint for user registration. It takes a user object as input, checks if a user with the same username already exists in the database, creates a new user record if not, generates an OTP secret key using pyotp, and then creates authentication data for the user.
    """

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


@auth_router.patch("/change_username", tags=["Auth"])
async def assign_username(
    username: str,
    token: str,
    db=Depends(get_db),
):
    """
    This function assigns a new username to a user and returns a new access token with the updated information.

    :param username: The `username` parameter in the `assign_username` function represents the new username that the user wants to assign to their account. This username will be updated in the database for the user associated with the provided token
    :type username: str
    :param token: The `token` parameter in the `assign_username` function is used to verify the user's identity and authorization. It is decoded using the `jwt.decode` method to extract the user's email address from the payload. This email address is then used to retrieve the user instance from the database
    :type token: str
    :param db: The `db` parameter in the code snippet represents the database connection or session. It is used to interact with the database to perform operations like querying, updating, or committing data. In this case, it is being used to update the username of a user in the database and commit the changes after the
    :return: a dictionary with the following keys and values:
    - "status" (missing a colon): This key is missing a colon and should be followed by a value.
    - "access_token": The access token generated for the user.
    - "token_type": The type of token, which is "bearer".
    - "expire_time": The expiration time of the access token.
    """

    payload = jwt.decode(
        token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
    )
    email: str = payload.get("sub")
    user_inst = await get_user_by_email(db, email)
    user_inst.username = str(username)
    access_token, expire_time = create_access_token(
        data={"sub": user_inst.email},
    )

    await db.commit()

    return {
        "status" "access_token": access_token,
        "token_type": "bearer",
        "expire_time": expire_time,
    }


@auth_router.get("/fetch", tags=["Auth"])
async def verify_token(token: str, db=Depends(get_db)):
    """
    This function verifies a JWT token, decodes it, retrieves user information from the database based on the token payload, and returns the user's details if found.

    :param token: The `token` parameter in the `verify_token` function is a string that represents the JWT token that needs to be decoded and verified. This token is passed as a query parameter in the GET request to the `/fetch` endpoint. The function attempts to decode the token using the `jwt.decode`
    :type token: str
    :param db: The `db` parameter in the `verify_token` function is a dependency that is used to get a database connection. It is obtained using the `Depends` function from FastAPI. In this case, the `get_db` function is likely a dependency that provides access to the database session within
    :return: The function `verify_token` returns a dictionary with either a status code of 200 and user information if the token is valid and the user exists in the database, or a status code of 401 and a flag indicating that the user is not logged in if the token is invalid or the user does not exist.
    """

    try:
        decoded_token = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )

        email = decoded_token.get("sub")
        if not isinstance(email, str):
            raise HTTPException(status_code=400, detail="Invalid token payload")
        user = await get_user_by_email(db, email)
        print(user)
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

    except JWTError:
        return {"status": 401, "is_user_logged_in": False}


@auth_router.get("/fetch/user", tags=["Auth"])
async def verify_user_token(token: str, username: str, db=Depends(get_db)):
    """
    This function verifies a user token and retrieves user information if the token is valid.

    :param token: The `token` parameter in the `verify_user_token` function is a string that represents the JWT token that will be used to verify the user's identity and access rights
    :type token: str
    :param username: The `username` parameter in the code snippet is used to specify the username of the user whose information is being fetched. It is passed as a parameter in the `verify_user_token` endpoint to retrieve user details based on the provided username
    :type username: str
    :param db: The `db` parameter in the code snippet is a dependency that is used to get a database connection. It is resolved by the `get_db` function which is likely defined elsewhere in the codebase. The `Depends` function is used to declare a dependency in FastAPI, and it ensures
    :return: If the token is successfully decoded and the user is found in the database, a JSON response will be returned with a status code of 200 and the user's information including username, email, and profile picture. If the user is not found in the database, a JSON response with a status code of 401 and "is_user_logged_in" set to False will be returned. If there is a
    """
    try:
        jwt.decode(token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM])

        user = await get_user_by_username(db, username)
        print(user)
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

    except JWTError:
        return {"status": 401, "is_user_logged_in": False}


@auth_router.get("/token/check", tags=["Auth"])
async def verify_token_check(token: str = Query(), db=Depends(get_db)):
    """
    This function verifies a JWT token and checks if the user associated with the token is logged in.

    :param token: The code snippet you provided is a FastAPI endpoint that checks the validity of a JWT token. The endpoint expects a `token` parameter in the query string. The function first checks if the token is not null or None. If the token is valid, it decodes the token using the provided secret
    :type token: str
    :param db: The `db` parameter in the `verify_token_check` function is a dependency that is used to get a database connection. It is obtained using the `Depends` function from the FastAPI framework. The `get_db` function is likely defined elsewhere in the codebase and is responsible for creating
    :return: The endpoint `/token/check` is checking the validity of a token provided in the query parameter. If the token is not null or None, it decodes the token using the specified secret key and algorithm. If the decoding is successful, it retrieves the user information associated with the token from the database and returns a response indicating that the user is logged in along with the user's ID, username, and
    """
    if token == "null" or token is None:
        return HTTPException(401, "token is null")
    try:
        decoded_token = jwt.decode(
            token, UsersConfig.SECRET_KEY, algorithms=[UsersConfig.ALGORITHM]
        )

        user = await get_user_by_email(db, str(decoded_token.get("sub")))
        if user:
            return {
                "status": 200,
                "is_user_logged_in": True,
                "user": [user.id, user.username, user.email],
            }
        return {"status": 401, "is_user_logged_in": False}

    except JWTError:
        return {"status": 401, "is_user_logged_in": False}


@auth_router.post("/token", tags=["Auth"])
async def login_for_access_token(
    email: str,
    password: str,
    google_token: str | None = None,
    db=Depends(get_db),
):
    """
    This Python function handles user authentication and generates an access token for a given email and password, with optional Google token authentication.

    :param email: The `email` parameter in the `login_for_access_token` function is a string that represents the user's email address. It is used as part of the authentication process to identify the user trying to log in
    :type email: str
    :param password: The `password` parameter in the `login_for_access_token` function is a required string parameter that represents the user's password. It is used for authenticating the user during the login process
    :type password: str
    :param google_token: The `google_token` parameter in the `login_for_access_token` function is an optional parameter that allows users to log in using their Google token for authentication. If a `google_token` is provided, the function will attempt to authenticate the user using both the email/password combination and the Google token
    :type google_token: str | None
    :param db: The `db` parameter in the code snippet is a dependency that is used to get the database connection. It is passed to the `login_for_access_token` function using `Depends(get_db)`. The `get_db` function is likely a dependency function that provides a database connection to the route
    :return: The function `login_for_access_token` returns a dictionary containing the access token, token type, and expiration time. The keys in the dictionary are "access_token", "token_type", and "expire_time".
    """
    if google_token:
        user = await authenticate_user(
            email=email,
            password=password,
            google_token=google_token,
            db=db,
        )
    user = await authenticate_user(
        email=email,
        password=password,
        db=db,
    )
    print(email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token, expire_time = create_access_token(
        data={"sub": user.email},
    )
    await set_user_online(db, user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expire_time": expire_time,
    }


@auth_router.post("/token/refresh", tags=["Auth"])
async def token_refresh(
    current_user: User = Depends(get_current_user),
):
    """
    This function generates a new access token for the current user during a token refresh operation.

    :param current_user: The `current_user` parameter in the `token_refresh` function is of type `User` and is obtained using the `Depends` function with the `get_current_user` dependency. This parameter represents the currently authenticated user making the request
    :type current_user: User
    :return: The function `token_refresh` is returning a dictionary with the keys "access_token", "token_type", and "status". The value of "access_token" is the newly created access token for the current user, the value of "token_type" is set to "bearer", and the value of "status" is set to 200.
    """
    try:
        access_token = create_access_token(data={"sub": current_user.username})

    except Exception as e:
        return {"error": e, "status": 500}

    return {"access_token": access_token, "token_type": "bearer", "status": 200}
