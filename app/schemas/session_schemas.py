from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class SessionCreate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    status: str
    started_at: datetime
    updated_at: Optional[datetime] = None
    supervisor_id: Optional[int] = None
    supervisor_name: Optional[str] = None


class AssignSupervisorRequest(BaseModel):
    supervisor_id: int


class AnswerEntry(BaseModel):
    question_key: str
    answer_value: Any


class SingleAnswerUpdate(BaseModel):
    question_key: str
    answer_value: Any


class SessionAnswersUpdate(BaseModel):
    answers: list[AnswerEntry]


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    answers: list[AnswerEntry]
