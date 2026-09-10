from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.config import get_settings
from app.schemas.schemas import TranscriptionOut
from app.services.auth import get_current_user
from app.services.ingestion import extract_from_audio

router = APIRouter(prefix="/api/transcribe", tags=["transcription"])
settings = get_settings()

AUDIO_SUFFIX_BY_MIME = {
    "audio/wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/webm": ".webm",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
}

MAX_AUDIO_BYTES = 15 * 1024 * 1024  # 15 MB — voice notes only, not long recordings


@router.post("", response_model=TranscriptionOut)
async def transcribe(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """Transcribes a short voice recording so the frontend can show it as an
    editable text box before the user submits a case — never analyzed
    directly from audio without the user seeing the words first."""
    content_type = file.content_type or ""
    if content_type not in AUDIO_SUFFIX_BY_MIME:
        raise HTTPException(status_code=415, detail=f"Unsupported audio type: {content_type}")

    content = await file.read()
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Recording is too long — please keep it under a couple of minutes.")

    suffix = AUDIO_SUFFIX_BY_MIME[content_type]
    result = extract_from_audio(content, suffix=suffix)

    if not result.text:
        raise HTTPException(
            status_code=422,
            detail="Could not make out any speech in that recording — please try again somewhere quieter.",
        )

    return TranscriptionOut(text=result.text, language=None)
