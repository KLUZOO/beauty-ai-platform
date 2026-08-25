from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Header,
    Depends
)
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

from database import (
    init_db,
    get_session
)

from conversation_store import (
    get_or_create_conversation,
    save_history
)

from gemini_client import run_conversation


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # The code here is executed WHEN the application STARTS
    await init_db()
    yield
    # The code here will be executed WHEN it STOPS (if something needs to be closed)


# Pass lifespan to FastAPI settings
app = FastAPI(title="Beauty AI Assistant", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


@app.post("/chat", response_model=ChatResponse)
async def chat(
        payload: ChatRequest,
        authorization: str | None = Header(default=None),
        session: AsyncSession = Depends(get_session),
):
    """
    **Frontend Integration Guide:**

    1. **Client Authorization:** If the client is logged in, the frontend must pass their JWT token
        in the "Authorization: Bearer <token>" header. This token is forwarded to DRF requests
        when an action is required on behalf of a specific client (e.g., creating a real booking).

    2. **Conversation History:** History is now safely stored on the backend server rather than
        being transmitted by the client every time. The client just needs to keep and send the
        "conversation_id" to continue the same chat session.
    """
    client_token = None
    if authorization and authorization.startswith("Bearer "):
        client_token = authorization.removeprefix("Bearer ")

    # Get or create a conversation in the database
    conversation = await get_or_create_conversation(
        session, payload.conversation_id, client_id=client_token
    )

    # Starting a conversation with Gemini
    result = await run_conversation(
        message=payload.message,
        history=conversation.history or [],
        client_token=client_token,
    )

    # Update the history in the conversation object (save_history
    # itself now simply flags the changes, and get_session will record them)
    await save_history(session, conversation, result["history"])

    # Cast the ID to a string str() to avoid Pydantic validation errors
    return {
        "reply": result["reply"],
        "conversation_id": str(conversation.id),
    }


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
