from asyncio.log import logger
import psycopg2
import sqlalchemy

import r3almX_backend
from r3almX_backend.database import init_db


@r3almX_backend.r3almX.on_event("startup")
async def init_database():
    try:
        await init_db()
    except (
        sqlalchemy.exc.OperationalError,
        psycopg2.OperationalError,
    ) as p:
        logger.error(f"database connection error: {p}")
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
