import datetime
import uuid
from typing import Any, Dict

from sqlalchemy import Column, DateTime, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.inspection import inspect

from r3almX_backend.auth_service.user_models import User
from r3almX_backend.database import AsyncSession, Base, metadata_obj


class DynamicModelMeta(DeclarativeMeta):
    def __new__(cls, name, bases, attrs):
        if "__tablename__" in attrs and "__table__" not in attrs:
            attrs["__table__"] = Table(
                attrs["__tablename__"], metadata_obj, *attrs.get("__table_args__", ())
            )
        return super().__new__(cls, name, bases, attrs)


class DynamicModelBase(Base, metaclass=DynamicModelMeta):
    __abstract__ = True

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for c in inspect(self.__class__).mapper.column_attrs:
            value = getattr(self, c.key, None)
            if isinstance(value, uuid.UUID):
                result[c.key] = str(value)
            elif isinstance(value, datetime.datetime):
                result[c.key] = value.isoformat()
            else:
                result[c.key] = str(value)
        return result


def get_dynamic_model(table_name: str, columns: list[Column]) -> Any:
    return type(
        f"DynamicModel_{table_name}",
        (DynamicModelBase,),
        {
            "__tablename__": table_name,
            "__table_args__": columns,
        },
    )


def get_channel_model(room_id: str) -> Any:
    table_name = f"channels_{room_id}"
    columns = [
        Column("id", UUID(as_uuid=True), primary_key=True),
        Column("channel_name", String()),
        Column("channel_description", String()),
        Column("author", UUID(as_uuid=True)),
        Column("time_created", DateTime(timezone=False), default=datetime.datetime.now),
    ]
    return get_dynamic_model(table_name, columns)


def get_message_model(room_id: str) -> Any:
    table_name = f"messages_{room_id}"
    columns = [
        Column("id", UUID(as_uuid=True), primary_key=True),
        Column("channel_id", UUID(as_uuid=True), ForeignKey(f"channels_{room_id}.id")),
        Column("sender_id", UUID(as_uuid=True), ForeignKey("users.id")),
        Column("message", String()),
        Column("timestamp", DateTime(timezone=False), default=datetime.datetime.now),
    ]
    return get_dynamic_model(table_name, columns)


async def insert_to_channels_table(
    room_id: str,
    db: AsyncSession,
    user: User,
    channel_name: str,
    channel_description: str,
) -> UUID:
    try:
        ChannelModel = get_channel_model(room_id)
        channel_id = uuid.uuid4()
        new_channel = ChannelModel(
            id=channel_id,
            channel_name=channel_name,
            channel_description=channel_description,
            author=user.id,
        )
        db.add(new_channel)
        await db.commit()
        return channel_id
    except Exception as e:
        await db.rollback()
        print(f"Error inserting channel: {e}")
        raise


async def insert_to_messages_table(
    room_id: str, db: AsyncSession, channel_id: str, user: User, message: str
) -> UUID:
    try:
        MessageModel = get_message_model(room_id)
        message_id = uuid.uuid4()
        new_message = MessageModel(
            id=message_id,
            channel_id=channel_id,
            sender_id=user.id,
            message=message,
        )
        db.add(new_message)
        await db.commit()
        return message_id
    except Exception as e:
        await db.rollback()
        print(f"Error inserting message: {e}")
        raise
