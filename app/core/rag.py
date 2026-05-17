from __future__ import annotations

import json
import re
from functools import lru_cache

from app.core.config import get_settings
from app.core.schemas import RagCitation, RagResponse


TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+")


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

    scored = sorted(
        ((_score_chunk(question, chunk), chunk) for chunk in load_chunks()),
        key=lambda item: item[0],
        reverse=True,
    )
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
    return RagResponse(question=question, answer=answer, citations=citations, backend="keyword-rag")


def _score_chunk(question: str, chunk: dict) -> float:
    query_terms = _terms(question)
    content = " ".join(
        [
            chunk.get("title", ""),
            chunk.get("section", ""),
            chunk.get("content", ""),
            " ".join(chunk.get("tags", [])),
        ]
    )
    content_terms = _terms(content)
    overlap = query_terms & content_terms
    tag_hits = query_terms & set(chunk.get("tags", []))
    exact_hits = sum(1 for term in query_terms if term and term in content)
    return len(overlap) * 1.0 + len(tag_hits) * 1.5 + exact_hits * 0.35


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
