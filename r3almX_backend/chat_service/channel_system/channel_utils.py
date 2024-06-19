import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, insert
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from r3almX_backend.database import *


def get_dynamic_model(table_name, columns):
    """
    Generate a dynamic ORM model class based on the table structure.

    Args:
        table_name (str): The name of the table.
        metadata (MetaData): The SQLAlchemy metadata object.
        columns (list): A list of column definitions for the table.

    Returns:
        A subclass of the declarative base class representing the table.
    """

    class DynamicModel(Base):
        __tablename__ = table_name
        __table__ = Table(table_name, metadata_obj, *columns, extend_existing=True)

    return DynamicModel


def get_channel_model(room_id):
    table_name = f"channels_{room_id}"
    columns = [
        Column("id", UUID(as_uuid=True), primary_key=True),
        Column("channel_name", String()),
        Column("channel_description", String()),
        Column("author", UUID(as_uuid=True)),
        Column("time_created", DateTime(), default=datetime.datetime.now(datetime.UTC)),
    ]
    return get_dynamic_model(table_name, columns)


def get_message_model(room_id):
    table_name = f"messages_{room_id}"
    columns = [
        Column("id", UUID(as_uuid=True), primary_key=True),
        Column("channel_id", UUID(as_uuid=True), ForeignKey(f"channels_{room_id}.id")),
        Column("sender_id", UUID(as_uuid=True), ForeignKey("users.id")),
        Column("message", String()),
        Column("timestamp", DateTime(), default=datetime.datetime.now(datetime.UTC)),
    ]
    return get_dynamic_model(table_name, columns)


def insert_to_channels_table(room_id, db, user, channel_name, channel_description):

    table = get_channel_model(room_id)
    channel_id = uuid.uuid4()

    stmt = insert(table).values(
        id=channel_id,
        channel_name=channel_name,
        channel_description=channel_description,
        author=user.id,
    )

    db.execute(stmt)
    db.commit()

    return channel_id


def delete_channel(room_id):
    try:
        table = get_channel_model(room_id)
        table.__table__.drop()
    except Exception as e:
        return e


def insert_to_messages_table(room_id, db, channel_id, user, message: str):

    table = get_message_model(room_id)

    # Generate UUID
    message_id = uuid.uuid4()

    # Construct the insert statement
    stmt = insert(table).values(
        id=message_id,
        channel_id=channel_id,
        sender_id=user.id,
        message=message,
    )

    # Execute the statement
    db.execute(stmt)
    db.commit()

    return message_id
