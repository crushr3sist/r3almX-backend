from typing import Literal, Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    email: str


class UserCreate(BaseModel):
    email: str
    password: str
    username: str
    google_id: Optional[str] = None
    profile_pic: Optional[str] = None


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    username: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"]


class OTPSetupRequest(BaseModel):
    otp_secret_key: str
