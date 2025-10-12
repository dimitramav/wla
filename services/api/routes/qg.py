from fastapi import APIRouter
from ..models.QG import QGRequest, QGResponse, Question, SourceSpan
import hashlib, random
from typing import List

router = APIRouter()

@router.post("/qg", response_model=QGResponse)
def qg(req: QGRequest):
    print("QG request:", req)
    mat = f"{req.hash}:{req.level}:{req.seed}"
    rnd = random.Random(int(hashlib.blake2b(mat.encode(), digest_size=8).hexdigest(), 16))

    mcq_n = int(req.mix.get("mcq", 10))
    yn_n = int(req.mix.get("yesno", 5))
    assert mcq_n + yn_n == 15, "mix must sum to 15"

    base = {k: 1.0 for k in (req.keywords or ["definitions", "symptoms", "coping"])}
    for w in (req.weak_keywords or []):
        if w.key in base:
            base[w.key] = max(base[w.key], float(w.weight))

    keys, weights = list(base.keys()), list(base.values())
    s = sum(weights) or 1.0
    probs = [w / s for w in weights]

    def pick_keyword():
        x, acc = rnd.random(), 0.0
        for k, p in zip(keys, probs):
            acc += p
            if x <= acc:
                return k
        return keys[-1]

    def span(i):
        p = 1 + (i % 4)
        return SourceSpan(doc="doc1.pdf", page_from=p, page_to=p, chunk_id=f"c{(i % 6)}")

    qs: List[Question] = []

    for i in range(mcq_n):
        kw = pick_keyword()
        qs.append(Question(
            id=f"q-{req.level}-mcq-{i+1}",
            kind="mcq",
            text=f"[{kw}] Which option aligns best with the material?",
            options=["A) …", "B) …", "C) …", "D) …"],
            correct="B) …",
            why="Because it matches the source text.",
            keywords=[kw],
            source_spans=[span(i)]
        ))

    for i in range(yn_n):
        kw = pick_keyword()
        qs.append(Question(
            id=f"q-{req.level}-yn-{i+1}",
            kind="yesno",
            text=f"[{kw}] True/False: The statement is supported by the text.",
            options=["Yes", "No"],
            correct=rnd.choice(["Yes", "No"]),
            why="Based on the information provided.",        
            keywords=[kw],
            source_spans=[span(100 + i)]
        ))

    rnd.shuffle(qs)
    return QGResponse(questions=qs)
