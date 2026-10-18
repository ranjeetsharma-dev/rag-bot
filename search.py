import re
from rank_bm25 import BM25Okapi
from db import get_all_chunks


def tokenize(text):
    return re.findall(r"\w+", text.lower())


IDS, DOCS, METAS = get_all_chunks()
bm25 = BM25Okapi([tokenize(d) for d in DOCS])
DOC_BY_ID = dict(zip(IDS, DOCS))

def bm25_search(query, sources=None, n=20):
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(range(len(IDS)), key=lambda i: scores[i], reverse=True)
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