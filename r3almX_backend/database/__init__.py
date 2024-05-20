import pathlib

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

path = pathlib.Path(__file__).parent.absolute()


SQLALCHEMY_DATABASE_URI1 = "postgresql://postgres:ronny@localhost:5432"
SQLALCHEMY_DATABASE_URI2 = "postgresql://postgres:postgrespw@postgres:5432"
SQLALCHEMY_DATABASE_URI3 = "postgresql://postgres:ronny@host.docker.internal:5432"


engine = create_engine(
    SQLALCHEMY_DATABASE_URI3,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata_obj = MetaData()

Base = declarative_base()
