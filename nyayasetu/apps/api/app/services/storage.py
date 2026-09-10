"""
Minimal storage interface so a real deployment can swap this for an
S3-compatible client without touching callers. Files are stored per-case so
deleting a case can remove its directory in one shot.
"""
import hashlib
import os
from pathlib import Path

from app.config import get_settings

settings = get_settings()


def _case_dir(case_id: str) -> Path:
    d = Path(settings.storage_dir) / case_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_file(case_id: str, filename: str, content: bytes) -> tuple[str, str]:
    """Returns (storage_key, sha256_hex)."""
    sha256 = hashlib.sha256(content).hexdigest()
    safe_name = f"{sha256[:12]}_{filename}"
    path = _case_dir(case_id) / safe_name
    with open(path, "wb") as f:
        f.write(content)
    storage_key = str(path.relative_to(settings.storage_dir))
    return storage_key, sha256


def read_file(storage_key: str) -> bytes:
    path = Path(settings.storage_dir) / storage_key
    with open(path, "rb") as f:
        return f.read()


def delete_case_files(case_id: str) -> None:
    d = Path(settings.storage_dir) / case_id
    if d.exists():
        for f in d.iterdir():
            f.unlink(missing_ok=True)
        d.rmdir()


def delete_file(storage_key: str) -> None:
    path = Path(settings.storage_dir) / storage_key
    path.unlink(missing_ok=True)
