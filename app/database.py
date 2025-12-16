from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
import os

# SQLite database URL
DATABASE_URL = "sqlite:///./ori_api.db"

# Server configuration
API_SERVER = os.getenv("API_SERVER", "http://localhost:8000")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def create_db_and_tables():
    """Create all tables in the database"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency for getting database sessions"""
    with Session(engine) as session:
        yield session