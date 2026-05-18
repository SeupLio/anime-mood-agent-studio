from __future__ import annotations

import json
import math
import re
from collections import Counter
from functools import lru_cache
from hashlib import blake2b

from app.core.config import get_settings
from app.core.schemas import RagCitation, RagResponse


TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+")
EMBED_DIM = 192


@lru_cache(maxsize=1)
def load_chunks() -> list[dict]:
    path = get_settings().rag_path
    chunks: list[dict] = []
    if not path.exists():
        return chunks
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def answer_question(question: str, limit: int = 4) -> RagResponse:
    question = question.strip()
    if not question:
        question = "维护补偿和客服回复需要注意什么？"

    scored = _retrieve_and_rerank(question)
    selected = [(score, chunk) for score, chunk in scored if score > 0][:limit]
    if not selected:
        selected = scored[:limit]

    citations = [
        RagCitation(
            chunk_id=chunk.get("chunk_id", ""),
            source_doc=chunk.get("source_doc", ""),
            title=chunk.get("title", ""),
            section=chunk.get("section", ""),
            score=round(score, 3),
            content=chunk.get("content", ""),
            tags=chunk.get("tags", []),
        )
        for score, chunk in selected
    ]
    answer = _compose_answer(question, citations)
    return RagResponse(question=question, answer=answer, citations=citations, backend="embedding-rerank-rag")


def _retrieve_and_rerank(question: str) -> list[tuple[float, dict]]:
    query_vector = _embed_text(question)
    candidates = []
    for chunk in load_chunks():
        content = _chunk_text(chunk)
        dense = _cosine(query_vector, _embed_text(content))
        keyword = _score_chunk(question, chunk)
        first_stage = dense * 2.2 + min(keyword / 8.0, 1.0)
        candidates.append((first_stage, chunk))

    top_candidates = sorted(candidates, key=lambda item: item[0], reverse=True)[:12]
    reranked = []
    for first_stage, chunk in top_candidates:
        rerank = _rerank_score(question, chunk)
        reranked.append((round(first_stage * 0.45 + rerank * 0.55, 4), chunk))
    return sorted(reranked, key=lambda item: item[0], reverse=True)


def _score_chunk(question: str, chunk: dict) -> float:
    query_terms = _terms(question)
    content = _chunk_text(chunk)
    content_terms = _terms(content)
    overlap = query_terms & content_terms
    tag_hits = query_terms & set(chunk.get("tags", []))
    exact_hits = sum(1 for term in query_terms if term and term in content)
    return len(overlap) * 1.0 + len(tag_hits) * 1.5 + exact_hits * 0.35


def _rerank_score(question: str, chunk: dict) -> float:
    query_terms = _terms(question)
    content = _chunk_text(chunk)
    content_terms = _terms(content)
    if not query_terms:
        return 0.0
    overlap = len(query_terms & content_terms) / max(len(query_terms), 1)
    phrase_hits = sum(1 for term in query_terms if len(term) >= 2 and term in content)
    tag_hits = len(query_terms & set(chunk.get("tags", [])))
    section_boost = 0.1 if any(term in chunk.get("section", "") for term in query_terms) else 0.0
    return min(3.0, overlap * 1.4 + phrase_hits * 0.12 + tag_hits * 0.28 + section_boost)


def _chunk_text(chunk: dict) -> str:
    return " ".join(
        [
            chunk.get("title", ""),
            chunk.get("section", ""),
            chunk.get("content", ""),
            " ".join(chunk.get("tags", [])),
        ]
    )


@lru_cache(maxsize=512)
def _embed_text(text: str) -> tuple[float, ...]:
    weights: Counter[int] = Counter()
    for token in _terms(text):
        digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % EMBED_DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        weights[bucket] += sign * (1.0 + min(len(token), 6) * 0.08)
    norm = math.sqrt(sum(value * value for value in weights.values())) or 1.0
    return tuple(round(weights[index] / norm, 6) for index in range(EMBED_DIM))


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _terms(text: str) -> set[str]:
    values = set(TOKEN_RE.findall(text.lower()))
    for i in range(len(text) - 1):
        pair = text[i : i + 2]
        if re.match(r"^[\u4e00-\u9fff]{2}$", pair):
            values.add(pair)
    return values


def _compose_answer(question: str, citations: list[RagCitation]) -> str:
    if not citations:
        return "知识库暂未命中相关规则，建议补充公告、客服或活动文档后再回答。"

    bullets = []
    for citation in citations[:3]:
        content = citation.content.replace("\n", " ")
        bullets.append(f"依据《{citation.source_doc}》{citation.section}：{content[:140]}")
    joined = "；".join(bullets)
    return f"针对“{question}”，可先按知识库给出有依据的答复：{joined}。"
