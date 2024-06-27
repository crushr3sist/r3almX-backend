import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from r3almX_backend.database import Base


class AuthData(Base):
    __tablename__ = "auth_data"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    otp_secret_key = Column(String, unique=True, index=True)
    mail_otp_enabled = Column(Boolean, default=False)
    sms_otp_enabled = Column(Boolean, default=False)

    user = relationship("User", back_populates="auth_data")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    email: str = Column(String, unique=True, index=True)
    username: str = Column(String, unique=True, index=True)
    hashed_password: str = Column(String)
    google_id = Column(String, unique=True, nullable=True)

    is_active: bool = Column(Boolean, default=True)
    rooms_joined: list = Column(ARRAY(String), default=[])

    auth_data = relationship("AuthData", back_populates="user")
    owned_rooms = relationship("RoomsModel", back_populates="owner")
    sent_messages = relationship("MessageModel", back_populates="sender")
