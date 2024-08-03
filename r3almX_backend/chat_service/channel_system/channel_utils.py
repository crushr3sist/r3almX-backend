import datetime
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, insert
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import relationship

from r3almX_backend.auth_service.user_models import User
from r3almX_backend.database import *


def get_dynamic_model(table_name, columns):
    """
    The function `get_dynamic_model` dynamically creates a SQLAlchemy model class based on the provided
    table name and columns.

    :param table_name: The `table_name` parameter is a string that represents the name of the table in
    the database for which you want to create a dynamic model. It will be used as the value for the
    `__tablename__` attribute in the `DynamicModel` class
    :param columns: The `columns` parameter in the `get_dynamic_model` function represents the columns
    that will be included in the dynamically created SQLAlchemy model. Each column is typically defined
    as an instance of a SQLAlchemy Column object, specifying the column name, data type, constraints,
    etc
    :return: The `get_dynamic_model` function returns a dynamically created SQLAlchemy model class based
    on the provided `table_name` and `columns`. The model class has a `to_dict` method that converts an
    instance of the model to a dictionary.
    """

    class DynamicModel(Base):
        __tablename__: str = table_name
        __table__: Table = Table(
            table_name, metadata_obj, *columns, extend_existing=True
        )

        def to_dict(self) -> dict:
            """Convert the model instance to a dictionary."""
            result = {}
            for c in inspect(self).mapper.column_attrs:
                value = getattr(self, c.key)
                if isinstance(value, uuid.UUID):
                    result[c.key] = str(value)
                elif isinstance(value, datetime.datetime):
                    result[c.key] = value.isoformat()
                else:
                    result[c.key] = value
            return result

    return DynamicModel


def get_channel_model(room_id: str) -> any:

    table_name = f"channels_{room_id}"
    columns = [
        Column("id", UUID(as_uuid=True), primary_key=True),
        Column("channel_name", String()),
        Column("channel_description", String()),
        Column("author", UUID(as_uuid=True)),
        Column("time_created", DateTime(timezone=False), default=datetime.now()),
    ]
    return get_dynamic_model(table_name, columns)


def get_message_model(room_id: str):

    table_name = f"messages_{room_id}"
    columns = [
        Column("id", UUID(as_uuid=True), primary_key=True),
        Column("channel_id", UUID(as_uuid=True), ForeignKey(f"channels_{room_id}.id")),
        Column("sender_id", UUID(as_uuid=True), ForeignKey("users.id")),
        Column("message", String()),
        Column("timestamp", DateTime(timezone=False), default=datetime.now()),
    ]
    return get_dynamic_model(table_name, columns)


async def insert_to_channels_table(
    room_id: str,
    db: AsyncSession,
    user: User,
    channel_name: str,
    channel_description: str,
):

    try:
        table = get_channel_model(room_id)
        channel_id = uuid.uuid4()
        stmt = insert(table).values(
            id=channel_id,
            channel_name=channel_name,
            channel_description=channel_description,
            author=user.id,
        )
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        print(e)
    return channel_id


async def insert_to_messages_table(
    room_id: str, db: AsyncSession, channel_id: str, user: User, message: str
):
    try:
        table = get_message_model(room_id)
        message_id = uuid.uuid4()
        stmt = insert(table).values(
            id=message_id,
            channel_id=channel_id,
            sender_id=user.id,
            message=message,
        )
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        print(e)
    return message_id
