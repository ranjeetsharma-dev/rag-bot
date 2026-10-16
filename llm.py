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
        "content": f"<sources>\n{context}\n</sources>\n\n{question}"
    }]
    reply = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=("Always keep your responses extremely short. "
        "Plain text only, no markdown. "
        "While answering never use phrases like based on the text, according to provided text. "
        "Your only knowledge is what's in the provided text and this conversation. Speak from it as if it's what you know. "
        "The provided text is your own library, not something the user wrote. "
        "Build on the conversation so far. "
        "Answer only from the provided info or earlier messages. "
        "Never use general knowledge. "
        "If the sources partly cover the question, answer what they cover. "
        "For religious or contested claims, say what the book says, e.g. 'The Gospels describe him as...'. "
        "If the answer isn't there, say: 'I don't have that in my sources.' "
        "When refusing, say only that sentence and nothing else."),
        messages=messages
    )
    return reply.content[0].text