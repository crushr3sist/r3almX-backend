import asyncio
import datetime
import uuid
from datetime import datetime

from sqlalchemy import insert

from r3almX_backend.chat_service.channel_system.channel_utils import get_message_model
from r3almX_backend.database import *


class DigestionBroker:
    def __init__(self, batch_size=10, flush_interval=5):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.message_batch = []
        self.lock = asyncio.Lock()
        self.db = None  # Initialize db as None initially
        self.flush_task = None  # Initialize flush task as None

    async def delete_message(self, message_id):
        if self.db is None:
            raise ValueError("Database session (db) is not set. Call set_db(db) first.")
        try:
            async with self.lock:
                table_name = None
                for msg in self.message_batch:
                    if msg["id"] == message_id:
                        table_name = msg["room_id"]
                        self.message_batch.remove(msg)
                        break
                if table_name is not None:
                    table = get_message_model(table_name)
                    stmt = table.delete().where(table.c.id == message_id)
                    self.db.execute(stmt)
                    self.db.commit()
                    print(f"Deleted message with id {message_id} from batch and DB\n")
                else:
                    print(f"Message with id {message_id} not found in batch\n")
        except Exception as e:
            print(f"Exception occurred in delete_message: {e}")

    def parse_timestamp(self, timestamp_str: str) -> datetime:
        # Define the format based on the JavaScript format: "YYYY-MM-DD HH:MM:SS AM/PM"
        format_str = "%Y-%m-%d %I:%M:%S %p"

        # Parse the timestamp string into a datetime object
        try:
            parsed_datetime = datetime.strptime(timestamp_str, format_str)
            return parsed_datetime
        except ValueError as e:
            print(f"Error parsing timestamp: {e}")
            return None

    async def add_message(self, user_id, message):
        """
        - impliment a retry method for the message committing
        """
        if self.db is None:
            raise ValueError("Database session (db) is not set. Call set_db(db) first.")
        try:
            async with self.lock:
                msg_id = str(uuid.uuid4())
                print("add message: ", message, "\n")
                msg_data = {
                    "id": msg_id,
                    "channel_id": message["channel_id"],
                    "sender_id": user_id,
                    "message": message["message"],
                    "room_id": message["room_id"],
                    "timestamp": self.parse_timestamp(message["timestamp"]),
                }
                self.message_batch.append(msg_data)
                print(f"Added message to batch: {msg_data}\n")
                if len(self.message_batch) >= self.batch_size:
                    if self.flush_task is None or self.flush_task.done():
                        self.flush_task = asyncio.create_task(self.flush_to_db())
        except Exception as e:
            print("Exception occured in add message:", e)

    def set_db(self, db):
        self.db = db

    async def flush_to_db(self):
        if not self.message_batch:
            return

        async with self.lock:
            try:
                for msg in self.message_batch:
                    print(f"\n\n\n{msg}\n\n\n")
                    table_name = f"{msg['room_id']}"
                    table = get_message_model(table_name)
                    stmt = insert(table).values(
                        id=msg["id"],
                        sender_id=msg["sender_id"],
                        channel_id=msg["channel_id"],
                        message=msg["message"],
                        timestamp=msg["timestamp"],
                    )
                    print(f"Executing statement: {stmt}")
                    self.db.execute(stmt)
                self.db.commit()
                print(f"Flushed {len(self.message_batch)} messages to DB\n")
                self.message_batch.clear()
            except Exception as e:
                print(f"Exception occurred in flush db: {e}")
                self.db.rollback()

    async def start_flush_scheduler(self):
        try:
            while True:
                await asyncio.sleep(self.flush_interval)
                await self.flush_to_db()
        except Exception as e:
            print(f"Error in start_flush_scheduler: {e}")
