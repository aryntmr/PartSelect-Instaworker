"""Chat request and response models."""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from models.part import PartCard


class ChatMessage(BaseModel):
    """Single message in conversation history."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Incoming chat request."""

    message: str = Field(
        ...,
        min_length=1,
        description="User's search query or question",
        examples=["ice maker parts", "door seal for refrigerator", "dishwasher pump"]
    )
    history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Conversation history (previous messages)"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Optional conversation ID for tracking chat history"
    )
    
    @field_validator('message')
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class ChatMetadata(BaseModel):
    """Metadata for chat response."""
    
    type: str
    count: int = 0
    products: List[PartCard] = []


class ChatResponse(BaseModel):
    """Outgoing chat response."""
    
    reply: str
    metadata: ChatMetadata
