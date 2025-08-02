import base64
import uuid
from typing import Never

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from r3almX_backend.database import Base


class RoomsModel(Base):
    __tablename__: str = "rooms"
    id: str | Column[uuid.UUID] = Column(
        UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True
    )
    room_owner: Column[uuid.UUID] | str = Column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    room_name: str | Column[str] = Column(String())
    invite_key: str | Column[str] = Column(String())
    members: list[Never | str] | Column[Never] = Column(ARRAY(String), default=[])
    owner = relationship("User", back_populates="owned_rooms")
    channels = relationship("ChannelsModel", back_populates="room")

    def __init__(self, room_owner: str, room_name: str):
        self.room_owner = room_owner
        self.room_name = room_name
        self.members = list(self.room_owner)
        self.invite_key = base64.urlsafe_b64encode(uuid.uuid4().bytes)[:8].decode(
            "utf-8"
        )
