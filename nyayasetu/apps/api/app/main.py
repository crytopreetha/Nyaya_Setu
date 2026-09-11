import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db import Base, engine, SessionLocal
from app.routes import auth, cases, files, sources, referrals, drafts, transcribe, lawyers
from app.services.kb_loader import load_knowledge_base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nyayasetu")

app = FastAPI(title="NyayaSetu API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # prototype only — restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Every endpoint returns a request identifier for troubleshooting,
    without exposing internals in error responses (Section 10)."""
    request_id = str(uuid.uuid4())
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled error [request_id=%s]", request_id)
        return JSONResponse(
            status_code=500,
            content={"detail": "Something went wrong on our end.", "request_id": request_id},
        )
    response.headers["X-Request-Id"] = request_id
    return response


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        load_knowledge_base(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(files.router)
app.include_router(sources.router)
app.include_router(referrals.router)
app.include_router(drafts.router)
app.include_router(transcribe.router)
app.include_router(lawyers.router)
