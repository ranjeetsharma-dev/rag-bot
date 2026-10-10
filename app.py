import chromadb
from pydantic import BaseModel
from dotenv import load_dotenv
from anthropic import Anthropic
from fastapi import FastAPI
import json

load_dotenv()
client = Anthropic()

db = chromadb.PersistentClient(path = "db")
collection = db.get_or_create_collection("docs")
sessions = {}

app = FastAPI()

class Question(BaseModel):
    question: str
    session_id: str

def get_sources():
    data = collection.get(include=["metadatas"])
    return sorted({m["source"] for m in data["metadatas"] if m})    

def rewrite_query(history, question, sources):
    recent = "\n".join(f"{m['role']}: {m['content'][-300:]}" for m in history[-4:])
    r = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=(
            "Rewrite the latest question as a short standalone search query. Fix typos. "
            "Only use the conversation to resolve vague references. If it's a new topic, keep its topic. "
            f"Pick the most relevant file from: {sources}, or null if unsure. "
            'Reply only with JSON: {"query": "...", "source": "..."} (source can be null)'
        ),
        messages=[{"role": "user", "content": f"Conversation:\n{recent}\n\nLatest question: {question}"}]
    )
    text = r.content[0].text
    try:
        out = json.loads(text[text.find("{"):text.rfind("}") + 1])
        return out["query"], out.get("source")
    except Exception as e:
        print("rewrite failed:", e, text)
        return question, None

@app.post("/ask")
def ask(q:Question):
    history = sessions.setdefault(q.session_id, [])
    sources = get_sources()
    search_query, source = rewrite_query(history, q.question, sources)
    where = {"source": source} if source in sources else None
    results = collection.query(query_texts=[search_query], n_results=5, where=where)
    docs = results["documents"][0]
    dists = results["distances"][0]
    print(q.question, "→", search_query, source, dists)
    context = "\n\n".join(d for d, dist in zip(docs, dists) if dist < 1.3)

    messages = history[-20:] + [{
        "role": "user",
        "content": f"Relevant content:\n\n{context}\n\nQuestion: {q.question}"
    }]

    reply = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system="Build on the conversation so far. Answer only from the provided info or earlier messages. Never use general knowledge. If the answer isn't there, say: 'I don't have that in your files.'",
        messages=messages
    )
    answer = reply.content[0].text
    history.append({"role": "user", "content": q.question})
    history.append({"role": "assistant", "content": answer})    
    return {"answer": answer}