from pypdf import PdfReader
from config import CHUNK_SIZE, CHUNK_OVERLAP


def read_file(path):
    if path.lower().endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(path, errors = "ignore", encoding = "utf-8") as f:
        return f.read()

def split_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start<len(text):
        chunks.append(text[start: start+size])
        start += size-overlap
    return chunks
