import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from r3almX_backend.database import Base


class ChannelsModel(Base):
    __tablename__ = "channels"
    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"))
    channel_name = Column(String())
    channel_description = Column(String())
    time_created = Column(DateTime(), default=datetime.datetime.now(datetime.UTC))
    author = Column(UUID(as_uuid=True))
    room = relationship("RoomsModel", back_populates="channels")
    messages = relationship(
        "MessageModel", back_populates="channel", cascade="all, delete-orphan"
    )


class MessageModel(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    channel_id = Column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE")
    )
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    message = Column(String())
    timestamp = Column(DateTime(), default=datetime.datetime.now(datetime.UTC))
    channel = relationship("ChannelsModel", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")
