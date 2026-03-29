import json
from fastapi import APIRouter, HTTPException
from ..models.QG import QGRequest, QGResponse, Question, SourceSpan
from fastapi import  Query

from rag.qg import generate_qg

router = APIRouter()

@router.post("/qg", response_model=QGResponse)
def qg(req: QGRequest, topic: str = Query(...)):
     

    # For MVP we ignore weak_keywords and difficulty_profile here
    try:
        out = generate_qg(
            topic=topic,
            docset_hash=req.hash,
            mix=req.mix,
            seed=req.seed,            # string seed → converted inside generator
            keywords=req.keywords,
            weak_keywords=req.weak_keywords,
            weak_focus_ratio=req.weak_focus_ratio,
            difficulty_profile=req.difficulty_profile,
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM generated malformed JSON.")
    if not out["questions"]:
        raise HTTPException(status_code=422, detail="Not enough sources found for that topic. Please broaden your scope or try another topic.")
    # Conform exactly to QGResponse
    return QGResponse(questions=[
        Question(
            id=q["id"],
            kind=q["kind"],                    # "mcq"|"yesno"
            text=q["text"],
            options=q["options"],
            correct=q["correct"],
            why=q["why"],
            keywords=q["keywords"],
            source_spans=[SourceSpan(**s) for s in q["source_spans"]],
        )
        for q in out["questions"]
    ])
