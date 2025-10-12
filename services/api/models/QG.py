from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class SourceSpan(BaseModel):
    doc: str
    page_from: int
    page_to: int
    chunk_id: str

class WeakK(BaseModel):
    key: str
    weight: float

class QGRequest(BaseModel):
    hash: str
    level: int
    keywords: List[str] = Field(default_factory=list)
    mix: dict
    seed: str
    difficulty_profile: dict
    weak_keywords: Optional[List[WeakK]] = Field(default_factory=list)

class Question(BaseModel):
    id: str
    kind: Literal["mcq", "yesno"]
    text: str
    options: Optional[List[str]] = None
    correct: str
    why: str = ""
    keywords: List[str]
    source_spans: List[SourceSpan]

class QGResponse(BaseModel):
    questions: List[Question]
