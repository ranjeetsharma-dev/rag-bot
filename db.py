import chromadb
from config import DB_PATH, COLLECTION_NAME, BATCH_SIZE


db = chromadb.PersistentClient(path=DB_PATH)
collection = db.get_or_create_collection(COLLECTION_NAME)

def get_all_chunks():
    ids, docs, metas = [], [], []
    offset = 0
    while True:
        batch = collection.get(include=["documents", "metadatas"], limit=BATCH_SIZE, offset=offset)
        if not batch["ids"]:
            break
        ids += batch["ids"]
        docs += batch["documents"]
        metas += batch["metadatas"]
        offset += BATCH_SIZE

    return ids, docs, metas