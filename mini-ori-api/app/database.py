import os

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mini_ori_api.db")
API_PREFIX = "/ori-mock"
API_SERVER = os.getenv("API_SERVER", f"http://localhost:8000{API_PREFIX}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
