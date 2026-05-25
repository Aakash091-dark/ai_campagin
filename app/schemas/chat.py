from typing import Optional

from pydantic import BaseModel
from pydantic import Field


# =========================================================
# CHAT REQUEST
# =========================================================
class ChatRequest(BaseModel):

    # workspace_id is now OPTIONAL.
    # If omitted, the backend will resolve it from the
    # authenticated user's database record.
    workspace_id: Optional[int] = None

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )

    conversation_id: Optional[str] = None

    user_id: Optional[int] = None


# =========================================================
# CHAT RESPONSE
# =========================================================
class ChatResponse(BaseModel):

    success: bool

    conversation_id: str

    openui_response: str

    execution_time: float

    agent_used: Optional[str] = None

    tokens_used: int = 0