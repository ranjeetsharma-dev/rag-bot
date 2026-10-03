import chromadb
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic()

db = chromadb.PersistentClient(path="db")
collection = db.get_or_create_collection("docs")

history = []

while True:
    question = input("\nAsk (or 'quit'): ")
    if question.lower() == "quit":
        break

    results = collection.query(query_texts=[question], n_results=5)
    context = "\n\n".join(results["documents"][0])

    history.append({
        "role": "user",
        "content": f"Relevant info:\n\n{context}\n\nQuestion: {question}"
    })

    reply = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system="Answer using only the info provided. If it's not there, say so.",
        messages=history
    )

    answer = reply.content[0].text
    print(answer)
    history.append({"role": "assistant", "content": answer})