from fastapi import FastAPI,Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import N_RESULTS, MAX_DISTANCE
from db import collection, get_sources
from llm import rewrite_query, answer
from models import Question

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
SOURCES = get_sources()  
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

    search_query, source = rewrite_query(history, q.question, SOURCES)
    if source in SOURCES:
        if source.startswith("mahabharata"):
            vols = [s for s in SOURCES if s.startswith("mahabharata")]
            where = {"source": {"$in": vols}}
        else:
             where = {"source": source}
    else:
        where = None

    results = collection.query(query_texts=[search_query], n_results=N_RESULTS, where=where)
    docs = results["documents"][0]
    dists = results["distances"][0]
    print(q.question, "→", search_query, source, dists)
    context = "\n\n".join(d for d, dist in zip(docs, dists) if dist < MAX_DISTANCE)

    reply = answer(history, context, q.question)
    history.append({"role": "user", "content": q.question})
    history.append({"role": "assistant", "content": reply})
    return {"answer": reply}