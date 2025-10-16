from fastapi import APIRouter, HTTPException
from ..models.QG import QGRequest, QGResponse, Question, SourceSpan
from fastapi import  Query

from rag.qg import generate_qg

router = APIRouter()

@router.post("/qg", response_model=QGResponse)
def qg(req: QGRequest, topic: str = Query(...)):
     

    # For MVP we ignore weak_keywords and difficulty_profile here
    out = generate_qg(
        topic=topic,
        docset_hash=req.hash,
        mix=req.mix,
        seed=req.seed,            # string seed → converted inside generator
        keywords=req.keywords,
    )
    if not out["questions"]:
        raise HTTPException(409, "No chunks available for this hash. Did you ingest this topic?")
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
