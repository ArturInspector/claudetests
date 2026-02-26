from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    topic: str = Field(min_length=3, max_length=255)
    level: str | None = Field(default=None, max_length=50)


class SessionRead(BaseModel):
    id: int
    topic: str
    level: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SessionSummary(SessionRead):
    iteration_count: int = 0
    message_count: int = 0


class IterationRead(BaseModel):
    id: int
    number: int
    question: str
    answer: str
    feedback: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: UUID
    session_id: int
    role: str
    content: str
    analysis_json: dict | None = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionDetail(SessionRead):
    iterations: List[IterationRead]
    messages: List[MessageResponse] = []


class AnswerRequest(BaseModel):
    question: str = Field(min_length=3)
    answer: str = Field(min_length=3)


class AnswerResponse(BaseModel):
    iteration: IterationRead
    similar_context: list[str] = []

