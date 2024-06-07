from email.utils import parseaddr
from uuid import UUID

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..database import SessionLocal
from . import user_models, user_schemas

password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_user(db: Session, user_id):
    return db.query(user_models.User).filter(user_models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    if check_records := (
        db.query(user_models.User).filter(user_models.User.username == username).first()
    ):
        return check_records
    return False


def hash_password(password):
    return password_context.hash(password)


def verify_password(raw_password, hashed_password):
    return password_context.verify(raw_password, hashed_password)


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(user_models.User).offset(skip).limit(limit).all()


def check_email(email: str):
    return email if parseaddr(email)[1] else False


def set_user_online(db, user_id: str):
    user = db.query(user_models.User).filter(user_models.User.id == user_id).first()
    user.is_active = True
    db.commit()


def set_user_offline(db, user_id: str):
    user = db.query(user_models.User).filter(user_models.User.id == user_id).first()
    user.is_active = False
    db.commit()


def create_user(db: Session, user: user_schemas.UserCreate):
    email: str = check_email(user.email)
    hashed_password: str = hash_password(user.password)
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=400, detail="User with this username already exists"
        )

    db_user = user_models.User(
        email=email, hashed_password=hashed_password, username=user.username
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_auth_data(db: Session, user_id: str, otp_secret_key: str):
    auth_data = user_models.AuthData(otp_secret_key=otp_secret_key, user_id=user_id)
    db.add(auth_data)
    db.commit()
    db.refresh(auth_data)
    return auth_data


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
