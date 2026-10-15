import chromadb
from config import DB_PATH, COLLECTION_NAME, BATCH_SIZE


db = chromadb.PersistentClient(path=DB_PATH)
collection = db.get_or_create_collection(COLLECTION_NAME)

def get_sources():
    sources = set()
    offset = 0
    while True:
        batch = collection.get(include=["metadatas"], limit=BATCH_SIZE, offset=offset)["metadatas"]
        if not batch:
            break
        sources.update(m["source"] for m in batch)
        offset += BATCH_SIZE
    
    return sorted(sources)
