"""
Extraction order, per Section 7.2:
1. Read embedded text from a digital PDF.
2. If extracted text is insufficient, render pages and run OCR.
3. Normalize whitespace without destroying paragraph boundaries.
4. Preserve page numbers where available.
5. Mark low-quality pages for user review.
"""
import io
import re
from dataclasses import dataclass, field

MIN_CHARS_PER_PAGE_BEFORE_OCR = 40


@dataclass
class ExtractionResult:
    text: str
    method: str  # native_text | ocr | manual_text
    quality_score: float
    low_quality_pages: list[int] = field(default_factory=list)


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_from_text(raw_text: str) -> ExtractionResult:
    text = _normalize_whitespace(raw_text)
    return ExtractionResult(text=text, method="manual_text", quality_score=1.0)


def extract_from_pdf(content: bytes) -> ExtractionResult:
    import fitz  # PyMuPDF

    doc = fitz.open(stream=content, filetype="pdf")
    pages_text = []
    low_quality_pages = []
    used_ocr = False

    for i, page in enumerate(doc):
        native = page.get_text("text") or ""
        if len(native.strip()) >= MIN_CHARS_PER_PAGE_BEFORE_OCR:
            pages_text.append(f"[page {i + 1}]\n{native.strip()}")
            continue

        # Fallback: render the page and OCR it.
        used_ocr = True
        try:
            import pytesseract
            from PIL import Image

            pix = page.get_pixmap(dpi=250)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text = pytesseract.image_to_string(img, lang="eng+hin")
        except Exception:
            ocr_text = ""

        if len(ocr_text.strip()) < MIN_CHARS_PER_PAGE_BEFORE_OCR:
            low_quality_pages.append(i + 1)
        pages_text.append(f"[page {i + 1}]\n{ocr_text.strip()}")

    full_text = _normalize_whitespace("\n\n".join(pages_text))
    total_pages = max(len(doc), 1)
    quality_score = 1.0 - (len(low_quality_pages) / total_pages)

    return ExtractionResult(
        text=full_text,
        method="ocr" if used_ocr else "native_text",
        quality_score=round(quality_score, 2),
        low_quality_pages=low_quality_pages,
    )


def extract_from_image(content: bytes) -> ExtractionResult:
    import pytesseract
    from PIL import Image

    img = Image.open(io.BytesIO(content))
    text = pytesseract.image_to_string(img, lang="eng+hin")
    quality_score = 1.0 if len(text.strip()) >= MIN_CHARS_PER_PAGE_BEFORE_OCR else 0.3
    low_quality_pages = [] if quality_score >= 1.0 else [1]
    return ExtractionResult(
        text=_normalize_whitespace(text),
        method="ocr",
        quality_score=quality_score,
        low_quality_pages=low_quality_pages,
    )


def extract_from_docx(content: bytes) -> ExtractionResult:
    import docx

    doc = docx.Document(io.BytesIO(content))
    text = "\n".join(p.text for p in doc.paragraphs)
    return ExtractionResult(text=_normalize_whitespace(text), method="native_text", quality_score=1.0)


def extract_from_audio(content: bytes, suffix: str = ".webm") -> ExtractionResult:
    """Transcribes audio with faster-whisper (runs locally, CPU-only, no API
    key needed — downloads the model weights once on first use). Section 6.2
    requires the transcript to be shown to the user for correction before
    analysis; the /api/transcribe route (routes/transcribe.py) is what the
    frontend calls to get that editable transcript up front."""
    import tempfile
    from pathlib import Path

    from app.config import get_settings
    from app.services.transcription import get_whisper_model

    settings = get_settings()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        model = get_whisper_model(settings.whisper_model_size)
        segments, info = model.transcribe(str(tmp_path), beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments).strip()
    finally:
        tmp_path.unlink(missing_ok=True)

    quality_score = 1.0 if len(text) >= MIN_CHARS_PER_PAGE_BEFORE_OCR else 0.4
    return ExtractionResult(
        text=_normalize_whitespace(text),
        method="asr",
        quality_score=quality_score,
        low_quality_pages=[] if quality_score >= 1.0 else [1],
    )


def extract(mime_type: str, content: bytes) -> ExtractionResult:
    if mime_type == "application/pdf":
        return extract_from_pdf(content)
    if mime_type in ("image/png", "image/jpeg", "image/jpg"):
        return extract_from_image(content)
    if mime_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        return extract_from_docx(content)
    if mime_type.startswith("audio/"):
        suffix = {
            "audio/wav": ".wav",
            "audio/mpeg": ".mp3",
            "audio/webm": ".webm",
            "audio/mp4": ".m4a",
            "audio/x-m4a": ".m4a",
        }.get(mime_type, ".webm")
        return extract_from_audio(content, suffix=suffix)
    raise ValueError(f"Unsupported file type for extraction: {mime_type}")
