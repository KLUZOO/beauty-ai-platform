"""
A proprietary, lightweight database just for the AI service that stores conversation history.
Not connected to the main Django database, as this data is needed exclusively here.
"""

import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import (
    Column,
    String,
    DateTime,
    JSON,
    func
)
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = "sqlite+aiosqlite:////app/data/conversations.db"


engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, nullable=True, index=True)
    history = Column(JSON, default=list)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


async def init_db() -> None:
    """Creates tables on application startup if they don't already exist."""
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """The session generator that FastAPI will use as Depends."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
