from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from konfwg.config import configuration

def database_url() -> str:
    return f"sqlite:///{configuration.DB_PATH}"

engine = create_engine(
    database_url(),
    connect_args = {"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)