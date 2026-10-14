import os
from config import EXTS, DOCS_DIR, BATCH_SIZE
from db import collection
from loader import read_file, split_text

files = [n for n in os.listdir(DOCS_DIR) if n.lower().endswith(EXTS)]

existing = collection.get(include=["metadatas"])["metadatas"]
stale = {m["source"] for m in existing if m and m.get("source")} - set(files)
if stale:
    collection.delete(where={"source":{"$in":list(stale)}})
    print(f"removed: {', '.join(sorted(stale))}")

for name in files:
    path = os.path.join(DOCS_DIR, name)
    text = read_file(path)
    chunks = [c.strip() for c in split_text(text) if c.strip()]
    collection.delete(where={"source":name})
    if not chunks:
        print(f"{name}: no text found, skipped.")
        continue
    
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i+BATCH_SIZE]
        collection.upsert(
            documents=batch,
            ids=[f"{name}-{j}" for j in range(i, i+ len(batch))],
            metadatas=[{"source": name} for _ in batch]
        )
    print(f"{name}: {len(chunks)} chunks")
