from email.utils import parseaddr
from typing import AsyncGenerator
import typing

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from r3almX_backend.auth_service.user_models import AuthData, User
from r3almX_backend.auth_service.user_schemas import UserCreate
from r3almX_backend.database import SessionLocal

password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


async def get_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


async def get_user_by_username(db: AsyncSession, username: str) -> User:
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> User:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


def hash_password(password):
    return password_context.hash(password)


async def verify_password(raw_password, hashed_password):
    return password_context.verify(raw_password, hashed_password)





def check_email(email: str):
    return email if parseaddr(email)[1] else False


async def set_user_online(db, user_id: str):
    user = db.query(User).filter(User.id == user_id).first()
    user.is_active = True
    db.commit()


async def set_user_offline(db, user_id: str):
    user = db.query(User).filter(User.id == user_id).first()
    user.is_active = False
    db.commit()


async def create_user_record(db: AsyncSession, user: UserCreate):
    email: str = check_email(user.email)
    hashed_password: str = hash_password(user.password)

    if await get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=400, detail="User with this username already exists"
        )

    db_user = User(
        email=email,
        hashed_password=hashed_password,
        username=user.username,
        google_id=user.google_id,
        profile_pic=user.profile_pic,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


async def create_auth_data(db: AsyncSession, user_id: str, otp_secret_key: str):
    auth_data = AuthData(otp_secret_key=otp_secret_key, user_id=user_id)
    db.add(auth_data)
    await db.commit()
    await db.refresh(auth_data)
    return auth_data


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
