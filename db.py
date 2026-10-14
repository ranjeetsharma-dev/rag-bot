import chromadb
from config import DB_PATH, COLLECTION_NAME

db = chromadb.PersistentClient(path=DB_PATH)
collection = db.get_or_create_collection(COLLECTION_NAME)

def get_sources():
    data = collection.get(include=["metadatas"])["metadatas"]
    return sorted({m["source"] for m in data if m and m.get("source")})
