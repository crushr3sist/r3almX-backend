import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from r3almX_backend.database import Base


def create_channel_table(room_id):
    table_name = f"channels_{room_id}"
    return Table(
        table_name,
        Base.metadata,
        Column(
            "id", UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True
        ),
        Column("channel_name", String()),
        Column("channel_description", String()),
        Column("time_created", DateTime(), default=datetime.datetime.now(datetime.UTC)),
        Column("author", UUID(as_uuid=True)),
    )


def create_message_table(room_id):
    table_name = f"messages_{room_id}"
    return Table(
        table_name,
        Base.metadata,
        Column(
            "id", UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True
        ),
        Column("channel_id", UUID(as_uuid=True), ForeignKey(f"channels_{room_id}.id")),
        Column("sender_id", UUID(as_uuid=True), ForeignKey("users.id")),
        Column("message", String()),
        Column("timestamp", DateTime(), default=datetime.datetime.now(datetime.UTC)),
    )
