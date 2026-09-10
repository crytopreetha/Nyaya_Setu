"""
Re-seeds the knowledge base into a running Postgres instance. Useful after
editing knowledge-base/sources.json or seed_chunks.jsonl.

Run inside the api container so it has the same Python env:
    docker compose exec api python /app/../../scripts/ingest_sources.py
or, simpler, just drop the `sources`/`source_chunks` tables and restart the
api container — it re-seeds automatically on startup when those tables are
empty (see app/services/kb_loader.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.db import SessionLocal  # noqa: E402
from app.models import Source, SourceChunk  # noqa: E402
from app.services.kb_loader import load_knowledge_base  # noqa: E402

if __name__ == "__main__":
    db = SessionLocal()
    try:
        deleted_chunks = db.query(SourceChunk).delete()
        deleted_sources = db.query(Source).delete()
        db.commit()
        print(f"Cleared {deleted_sources} sources and {deleted_chunks} chunks.")
        load_knowledge_base(db)
        print(f"Re-seeded: {db.query(Source).count()} sources, {db.query(SourceChunk).count()} chunks.")
    finally:
        db.close()
