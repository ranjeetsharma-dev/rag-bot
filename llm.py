import json
from dotenv import load_dotenv
from anthropic import Anthropic
from config import MODEL

load_dotenv()
client = Anthropic()


def rewrite_query(history, question, sources):
    recent = "\n".join(f"{m['role']}: {m['content'][-300:]}" for m in history[-4:])
    r = client.messages.create(
        model=MODEL,
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


def answer(history, context, question):
    messages = history[-20:] + [{
        "role": "user",
        "content": f"Relevant content:\n\n{context}\n\nQuestion: {question}"
    }]
    reply = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system="Build on the conversation so far. Answer only from the provided info or earlier messages. Never use general knowledge. If the answer isn't there, say: 'I don't have that in your files.'",
        messages=messages
    )
    return reply.content[0].text