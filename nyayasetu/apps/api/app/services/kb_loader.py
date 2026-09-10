import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Source, SourceChunk
from app.services.embeddings import embed_texts

settings = get_settings()


def load_knowledge_base(db: Session) -> None:
    kb_dir = Path(settings.knowledge_base_dir)
    sources_path = kb_dir / "sources.json"
    chunks_path = kb_dir / "seed_chunks.jsonl"

    if not sources_path.exists():
        return

    already_seeded = db.query(Source).count() > 0
    if already_seeded:
        return

    sources = json.loads(sources_path.read_text())
    for s in sources:
        db.add(
            Source(
                id=s["id"],
                title=s["title"],
                url=s["url"],
                publisher=s.get("publisher"),
                jurisdiction=s.get("jurisdiction"),
                topic=s.get("topic"),
                language=s.get("language", "en"),
                verification_status=s.get("verification_status", "unverified"),
            )
        )
    db.commit()

    if not chunks_path.exists():
        return

    raw_lines = [line for line in chunks_path.read_text().splitlines() if line.strip()]
    records = [json.loads(line) for line in raw_lines]

    try:
        vectors = embed_texts([r["text"] for r in records])
    except Exception:
        vectors = [None] * len(records)

    for record, vector in zip(records, vectors):
        db.add(
            SourceChunk(
                source_id=record["source_id"],
                content=record["text"],
                topic=record.get("topic"),
                embedding=vector,
            )
        )
    db.commit()
