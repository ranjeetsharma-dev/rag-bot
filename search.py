import re
import bm25s
from flashrank import Ranker, RerankRequest
from db import get_all_chunks


def tokenize(text):
    return re.findall(r"\w+", text.lower())


IDS, DOCS, METAS = get_all_chunks()
DOC_BY_ID = dict(zip(IDS, DOCS))

tokens = bm25s.tokenize(DOCS, token_pattern=r"(?u)\b\w+\b", stopwords=None, show_progress=False)
VOCAB = tokens.vocab
bm25 = bm25s.BM25(method="robertson")
bm25.index(tokens, show_progress=False)
del tokens

ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2")


def bm25_search(query, sources=None, n=20):
    q_ids = [VOCAB[t] for t in tokenize(query) if t in VOCAB]
    if not q_ids:
        return []
    scores = bm25.get_scores(q_ids)
    ranked = scores.argsort()[::-1]
    results = []
    for i in ranked:
        if scores[i] <= 0:
            break
        if sources is None or METAS[i]["source"] in sources:
            results.append(IDS[i])
            if len(results) == n:
                break
    return results


def rrf(*lists, k=60):
    scores = {}
    for ids in lists:
        for rank, cid in enumerate(ids, start=1):
            scores[cid] = scores.get(cid, 0) + 1 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)


def with_neighbors(ids):
    out = []
    for cid in ids:
        name, num = cid.rsplit("-", 1)
        for j in (int(num) - 1, int(num), int(num) + 1):
            nid = f"{name}-{j}"
            if nid in DOC_BY_ID and nid not in out:
                out.append(nid)
    return out


def rerank(query, ids, n):
    if not ids:
        return []
    passages = [{"id": cid, "text": DOC_BY_ID[cid]} for cid in ids]
    results = ranker.rerank(RerankRequest(query=query, passages=passages))
    return [r["id"] for r in results[:n]]