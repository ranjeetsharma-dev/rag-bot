from fastapi import FastAPI
from config import N_RESULTS, MAX_DISTANCE
from db import collection, get_sources
from llm import rewrite_query, answer
from models import Question

app = FastAPI()
sessions = {}


@app.post("/ask")
def ask(q: Question):
    history = sessions.setdefault(q.session_id, [])

    sources = get_sources()
    search_query, source = rewrite_query(history, q.question, sources)
    where = {"source": source} if source in sources else None

    results = collection.query(query_texts=[search_query], n_results=N_RESULTS, where=where)
    docs = results["documents"][0]
    dists = results["distances"][0]
    print(q.question, "→", search_query, source, dists)
    context = "\n\n".join(d for d, dist in zip(docs, dists) if dist < MAX_DISTANCE)

    reply = answer(history, context, q.question)
    history.append({"role": "user", "content": q.question})
    history.append({"role": "assistant", "content": reply})
    return {"answer": reply}