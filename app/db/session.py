# app/db/session.py
from sqlmodel import create_engine, Session, SQLModel

sqlite_file_name = "neuro_content.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)

def init_db() -> None:
    from app.db import models  # ensure models are imported
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)
