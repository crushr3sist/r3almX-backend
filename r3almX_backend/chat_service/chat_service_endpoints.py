from fastapi import Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from r3almX_backend.auth_service import user_handler_utils
from r3almX_backend.auth_service.auth_utils import TokenData
from r3almX_backend.auth_service.Config import UsersConfig
from r3almX_backend.auth_service.user_handler_utils import get_db, get_user_by_username
from r3almX_backend.chat_service.main import chat_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
""" 
this is where we connect users to channels
we need to write a **websocket handler** so multiple users
can poll messages in and out to certain channels

- write a feed websocket handler (client receiver)
- write a broadcast digest websocket handler (client  and message log updater)
- we need to specify which users to pool into which websocket
- we already specify the room id so the data knows where to be committed,
- we'll set a 50 message limit to be committed to the database 
    and stored in memory until committed
- and we'll poll whats being stored

"""


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)


def _get_current_user(
    token: str,
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


manager = ConnectionManager()


@chat_service.websocket("/feed/{room_id}/ws")
async def feed_ws_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str,
    db=Depends(get_db),
):
    user = _get_current_user(token, db)
    print(user)
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message text was: {data}", websocket)

    except WebSocketDisconnect:

        await manager.send_personal_message("Bye !!!", websocket)
        manager.disconnect(websocket)
