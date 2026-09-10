"""
Retrieval service. Searches the small curated `source_chunks` table (seeded
from knowledge-base/) using pgvector cosine distance. Falls back to a plain
keyword match if embeddings aren't available for some reason, so the
pipeline never silently returns nothing.
"""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SourceChunk, Source
from app.services.embeddings import embed_query

TOP_K = 5


@dataclass
class RetrievedChunk:
    source_id: str
    source_title: str
    source_url: str
    content: str
    score: float


def retrieve(db: Session, query: str, topic: str | None = None, top_k: int = TOP_K) -> list[RetrievedChunk]:
    stmt = select(SourceChunk, Source).join(Source, SourceChunk.source_id == Source.id)
    if topic:
        stmt = stmt.where(SourceChunk.topic == topic)
    rows = db.execute(stmt).all()

    if not rows:
        return []

    try:
        query_vec = embed_query(query)
        scored = []
        for chunk, source in rows:
            if chunk.embedding is None:
                continue
            # pgvector column returns as a list-like; cosine similarity via dot/norm
            import numpy as np

            v = np.array(chunk.embedding, dtype=float)
            q = np.array(query_vec, dtype=float)
            denom = (np.linalg.norm(v) * np.linalg.norm(q)) or 1e-9
            score = float(np.dot(v, q) / denom)
            scored.append((score, chunk, source))
        scored.sort(key=lambda t: t[0], reverse=True)
        top = scored[:top_k]
        if top:
            return [
                RetrievedChunk(
                    source_id=source.id,
                    source_title=source.title,
                    source_url=source.url,
                    content=chunk.content,
                    score=score,
                )
                for score, chunk, source in top
            ]
    except Exception:
        pass  # fall through to keyword search below

    # Keyword fallback
    query_terms = {w.lower() for w in query.split() if len(w) > 3}
    scored = []
    for chunk, source in rows:
        content_lower = chunk.content.lower()
        overlap = sum(1 for t in query_terms if t in content_lower)
        if overlap:
            scored.append((overlap, chunk, source))
    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:top_k]
    return [
        RetrievedChunk(
            source_id=source.id,
            source_title=source.title,
            source_url=source.url,
            content=chunk.content,
            score=float(overlap),
        )
        for overlap, chunk, source in top
    ]
