from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from rag.highlight import find_spans

router = APIRouter()


class HighlightRequest(BaseModel):
    topic: str
    doc: str
    text: str


class HighlightSpan(BaseModel):
    page: int
    bbox: List[float]
    score: float


class HighlightResponse(BaseModel):
    matches: List[HighlightSpan]


@router.post("/rag/highlight", response_model=HighlightResponse)
def highlight(req: HighlightRequest) -> HighlightResponse:
    spans = find_spans(req.topic, req.doc, req.text)
    return HighlightResponse(matches=[HighlightSpan(**s) for s in spans])
