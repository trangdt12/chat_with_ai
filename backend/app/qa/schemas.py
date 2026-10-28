import uuid
from typing import Literal

from pydantic import BaseModel


class ConversationOut(BaseModel):
    conversation_id: uuid.UUID


class QuestionIn(BaseModel):
    question: str


class CitationDetailOut(BaseModel):
    document_id: uuid.UUID
    filename: str
    page: int
    snippet: str


class FeedbackIn(BaseModel):
    rating: Literal["up", "down"]
    reason: Literal["wrong", "missing", "wrong_source", "other"] | None = None


class FeedbackOut(BaseModel):
    turn_id: uuid.UUID
    rating: Literal["up", "down"]
    reason: str | None
