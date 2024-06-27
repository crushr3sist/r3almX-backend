from typing import Literal

from pydantic import BaseModel


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str
    username: str
    google_id: str
    profile_pic: str


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True


class TokenData(BaseModel):
    username: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"]


class OTPSetupRequest(BaseModel):
    otp_secret_key: str
