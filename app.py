from fastapi import FastAPI,Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from settings import N_RESULTS, MAX_DISTANCE
from db import collection
from search import METAS, DOC_BY_ID, bm25_search, rrf, with_neighbors
from llm import rewrite_query, answer
from models import Question

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
SOURCES = sorted({m["source"] for m in METAS}) 
app.mount("/static", StaticFiles(directory="static"), name="static")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
sessions = {}


@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.post("/ask")
@limiter.limit("10/hour;30/day")
def ask(request:Request, q: Question):
    history = sessions.setdefault(q.session_id, [])

    search_query, source, passage = rewrite_query(history, q.question, SOURCES)
    if source in SOURCES:
        if source.startswith("mahabharata"):
            allowed = [s for s in SOURCES if s.startswith("mahabharata")]
        else:
            allowed = [source]
        where = {"source": {"$in": allowed}}
    else:
        allowed, where = None, None

    results = collection.query(query_texts=[passage], n_results=20, where=where)
    vec_ids = [cid for cid, dist in zip(results["ids"][0], results["distances"][0]) if dist < MAX_DISTANCE]
    bm25_ids = bm25_search(search_query + " " + passage, allowed, n=20)
    top_ids = rrf(vec_ids, bm25_ids)[:N_RESULTS]
    print(q.question, "→", search_query, source, "\nvec:", vec_ids[:5], "\nbm25:", bm25_ids[:5], "\ntop:", top_ids)
    context = "\n\n".join(DOC_BY_ID[cid] for cid in with_neighbors(top_ids))

    reply = answer(history, context, q.question, search_query)
    history.append({"role": "user", "content": q.question})
    history.append({"role": "assistant", "content": reply})
    return {"answer": reply}