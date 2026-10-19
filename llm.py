import json
from dotenv import load_dotenv
from anthropic import Anthropic
from settings import MODEL

load_dotenv()
client = Anthropic()


def rewrite_query(history, question, sources):
    recent = "\n".join(f"{m['role']}: {m['content'][-300:]}" for m in history[-4:])
    r = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=(
            "Rewrite the latest question as a short standalone search query. Fix typos. "
            "Only use the conversation to resolve vague references. If it's a new topic, keep its topic. "
            "Resolve indirect references (an author, a nickname, a description) to the specific book, chapter or name, e.g. 'Revelation 21 New Jerusalem measurement'. "
            f"Pick the most relevant file from: {sources}, or null if unsure. "
            "Also write 'passage': 2-3 sentences that would answer the query, in the style of the source text "
            "(e.g. King James Bible, old Mahabharata translation), with the book and verse reference if you know it. "
            'Reply only with JSON: {"query": "...", "source": "...", "passage":"..."} (source can be null)'
        ),
        messages=[{"role": "user", "content": f"Conversation:\n{recent}\n\nLatest question: {question}"}]
    )
    text = r.content[0].text
    try:
        out = json.loads(text[text.find("{"):text.rfind("}") + 1])
        query = out.get("query") or question
        return query, out.get("source"), out.get("passage") or query
    except Exception as e:
        print("rewrite failed:", e, text)
        return question, None, question


def answer(history, context, question, search_query):
    messages = history[-20:] + [{
        "role": "user",
                "content": f"<sources>\n{context}\n</sources>\n\nInterpreted as: {search_query}\n\n{question}"
    }]
    reply = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=("Always keep your responses extremely short. "
        "Plain text only, no markdown. "
        "While answering never use phrases like based on the text, according to provided text. "
         "Never mention that text is cut off or incomplete. "   
        "Your only knowledge is what's in the provided text and this conversation. Speak from it as if it's what you know. "
        "The provided text is your own library, not something the user wrote. "
        "Build on the conversation so far. "
        "Answer only from the provided info or earlier messages. "
        "Never use general knowledge. "
        "If the sources partly cover the question, answer what they cover. "
        "If the sources answer what the user clearly means, even in different words, answer it. "   
        "Use the 'Interpreted as' line to understand what the user means; their question may have typos. "      
        "If the latest message only asks to shorten or rephrase, rewrite your previous answer in 1-2 sentences. "   
        "For religious or contested claims, say what the book says, e.g. 'The Gospels describe him as...'. "
        "If asked why you don't have something or what your sources contain, say only: 'My search didn't find it. Try rephrasing or asking about a specific part.' "
        "If the answer isn't there, say: 'I don't have that in my sources.' "
        "When refusing, say only that sentence and nothing else."),
        messages=messages
    )
    return reply.content[0].text