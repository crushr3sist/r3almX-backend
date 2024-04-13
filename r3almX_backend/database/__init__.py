import pathlib

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

path = pathlib.Path(__file__).parent.absolute()


SQLALCHEMY_DATABASE_URI1 = "postgresql://postgres:ronny@localhost:5432"
SQLALCHEMY_DATABASE_URI2 = "postgresql://postgres:postgrespw@postgres:5432"
SQLALCHEMY_DATABASE_URI3 = "postgresql://postgres:postgrespw@host.docker.internal:5432"


engine = create_engine(
    SQLALCHEMY_DATABASE_URI1,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
