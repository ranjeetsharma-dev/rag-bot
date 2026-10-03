import os
import chromadb
from pypdf import PdfReader

db = chromadb.PersistentClient(path="db")
collection = db.get_or_create_collection("docs")

def read_file(path):
    if path.endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(path) as f:
        return f.read()

def split_text(text, size=500, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks

for name in os.listdir("docs"):
    path = os.path.join("docs", name)
    text = read_file(path)
    chunks = [c.strip() for c in split_text(text) if c.strip()]
    collection.upsert(
        documents=chunks,
        ids=[f"{name}-{i}" for i in range(len(chunks))]
    )
    print(f"{name}: {len(chunks)} chunks")