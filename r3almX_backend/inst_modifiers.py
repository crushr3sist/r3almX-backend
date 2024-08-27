import asyncio

import psycopg2
import sqlalchemy

import r3almX_backend
from r3almX_backend.database import init_db

MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds


@r3almX_backend.r3almX.on_event("startup")
async def init_database():
    for attempt in range(MAX_RETRIES):
        try:
            await init_db()
            print("Database connected successfully")
            return
        except (sqlalchemy.exc.OperationalError, psycopg2.OperationalError) as e:
            print(
                f"Database connection failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
            )
            if attempt < MAX_RETRIES - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)

    print("Failed to connect to the database after multiple attempts")
    # You might want to raise an exception here or handle the failure in some way
    # raise Exception("Failed to connect to the database after multiple attempts")
