from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.config import get_settings
from app.db import get_db
from app.models import Case, CaseFile, User
from app.services.auth import get_current_user
from app.services.storage import save_file, read_file, delete_file

router = APIRouter(prefix="/api/cases", tags=["files"])
settings = get_settings()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "audio/wav",
    "audio/mpeg",
    "audio/webm",
    "audio/mp4",
    "audio/x-m4a",
}


def _get_owned_case(db: Session, case_id: str, user: User) -> Case:
    case = db.get(Case, case_id)
    if not case or case.status == "deleted" or case.user_id != user.id:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/files")
async def upload_file(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
):
    case = _get_owned_case(db, case_id, current_user)

    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {content_type}")

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the maximum allowed size.")

    storage_key, sha256 = save_file(case_id, file.filename or "upload", content)

    case_file = CaseFile(
        case_id=case_id,
        storage_key=storage_key,
        original_filename=file.filename or "upload",
        sha256=sha256,
        mime_type=content_type,
        size=len(content),
    )
    db.add(case_file)
    case.input_type = "document"
    db.commit()
    db.refresh(case_file)

    return {
        "id": case_file.id,
        "original_filename": case_file.original_filename,
        "mime_type": case_file.mime_type,
        "size": case_file.size,
    }


@router.get("/{case_id}/files")
def list_files(case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Evidence locker listing — every file the user attached to this case."""
    _get_owned_case(db, case_id, current_user)
    files = db.query(CaseFile).filter(CaseFile.case_id == case_id).order_by(CaseFile.created_at).all()
    return [
        {
            "id": f.id,
            "original_filename": f.original_filename,
            "mime_type": f.mime_type,
            "size": f.size,
            "created_at": f.created_at,
        }
        for f in files
    ]


@router.get("/{case_id}/files/{file_id}/download")
def download_file(
    case_id: str,
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_case(db, case_id, current_user)
    case_file = db.get(CaseFile, file_id)
    if not case_file or case_file.case_id != case_id:
        raise HTTPException(status_code=404, detail="File not found for this case")

    content = read_file(case_file.storage_key)
    return StreamingResponse(
        io.BytesIO(content),
        media_type=case_file.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{case_file.original_filename}"'},
    )


@router.delete("/{case_id}/files/{file_id}", status_code=204)
def delete_case_file(
    case_id: str,
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_case(db, case_id, current_user)
    case_file = db.get(CaseFile, file_id)
    if not case_file or case_file.case_id != case_id:
        raise HTTPException(status_code=404, detail="File not found for this case")

    delete_file(case_file.storage_key)
    db.delete(case_file)
    db.commit()
    return None
