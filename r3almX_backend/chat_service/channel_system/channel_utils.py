import uuid

from sqlalchemy import Table, insert

from r3almX_backend.database import *


def insert_to_channels_table(room_id, db, user, channel_name, channel_description):
    table_name = f"channels_{room_id}"
    table = Table(table_name, metadata_obj, autoload_with=engine)
    stmt = insert(table).values(
        channel_name=channel_name,
        channel_description=channel_description,
        author=user.id,
        id=str(uuid.uuid4()),
    )

    db.execute(stmt)
    db.commit()
    db.refresh(stmt)


def insert_to_messages_table(room_id, db, channel_id, user, message: str):
    table_name = f"messages_{room_id}"
    table = Table(table_name, metadata_obj, autoload_with=engine)
    stmt = insert(table).values(
        id=uuid.uuid4(), sender=user.id, channel_id=channel_id, message=message
    )

    db.execute(stmt)
    db.commit()
    db.refresh(stmt)
