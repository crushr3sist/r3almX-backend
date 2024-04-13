import base64
import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from r3almX_backend.chat_service.models.rooms_table import (
    create_channel_table,
    create_message_table,
)
from r3almX_backend.database import Base


class RoomsModel(Base):
    __tablename__ = "rooms"
    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    room_owner = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    room_name = Column(String())
    invite_key = Column(String())
    members = Column(ARRAY(String), default=[])
    owner = relationship("User", back_populates="owned_rooms")
    channels = relationship("ChannelsModel", back_populates="room")

    def __init__(self, room_owner: uuid.uuid4, room_name: str):
        self.room_owner = room_owner
        self.room_name = room_name
        self.members = [self.room_owner]
        self.invite_key = base64.urlsafe_b64encode(uuid.uuid4().bytes)[:8].decode(
            "utf-8"
        )
