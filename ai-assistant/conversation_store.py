"""
Simple functions for reading/writing conversation history to the database.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from database import Conversation


async def get_or_create_conversation(
        session: AsyncSession, conversation_id: str | None, client_id: str | None
) -> Conversation:
    if conversation_id:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            return conversation

    # if conversation_id was not passed, or there is no such conversation yet — create a new one
    conversation = Conversation(client_id=client_id, history=[])
    session.add(conversation)
    await session.flush()  # Generates a UUID for a new conversation
    return conversation


async def save_history(
        session: AsyncSession, conversation: Conversation, history: list[dict]
) -> None:
    # Writing a new story
    conversation.history = history

    # FORCEDLY tell SQLAlchemy: "The JSON field has changed, it must be saved!"
    flag_modified(conversation, "history")

    # Save changes to the database
    await session.commit()
