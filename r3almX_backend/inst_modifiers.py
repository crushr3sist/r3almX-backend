from asyncio.log import logger

import psycopg2
import sqlalchemy

from r3almX_backend import r3almX
from r3almX_backend.database import init_db


@r3almX.on_event("startup")
async def init_database():
    try:
        print("connected to db")
        await init_db()
    except (
        sqlalchemy.exc.OperationalError,
        psycopg2.OperationalError,
    ) as p:
        logger.error(f"database connection error: {p}")
        print("there was an error in the connection")
        for _ in range(0, 5):
            try:
                await init_db()
            except (
                sqlalchemy.exc.OperationalError,
                psycopg2.OperationalError,
            ) as p:
                print("db connection hitch, retrying")
            else:
                break
        raise Exception("Your db failed to connect bre")
