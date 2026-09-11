# NyayaSetu — Working Prototype

Preventive legal-risk and action-management platform. This is a runnable MVP
implementing the workflow in `nyayasetu-prototype-tech-stack.pdf`:

upload/describe → extract text → extract facts & dates → retrieve verified
sources → grounded explanation → risk labels → deadlines → action plan → draft.

## What's actually implemented (MVP scope)

To keep this runnable end-to-end without external infra, a few things from the
full spec are intentionally simplified. Each is called out so you know what to
harden before a real deployment:

| Spec item | MVP implementation | Upgrade path |
|---|---|---|
| Celery + Redis background workers | FastAPI `BackgroundTasks` (in-process) | Swap `analysis_pipeline.run_async` for a Celery task |
| Auth (JWT) | **Real signup/login.** Passwords hashed with bcrypt, JWT issued on `/api/auth/signup` and `/api/auth/login`, every case route requires `Authorization: Bearer <token>` and checks case ownership (`routes/cases.py::_get_owned_case`). | Add password reset, email verification, refresh tokens |
| Speech-to-text | **Wired up.** `/api/transcribe` runs `faster-whisper` (local, CPU, no API key — downloads model weights once on first use) on a short voice recording and returns an editable transcript, shown to the user before they submit a case (Section 6.2's "show transcript before analysis" requirement). Audio files uploaded directly as a case document also get transcribed automatically in the pipeline. | Swap to Bhashini ASR for better Hindi/regional-language accuracy |
| Object storage | Local disk under `apps/api/storage_data/` | Swap `services/storage.py` for S3-compatible client (same interface) |
| Embeddings | Local, offline via `fastembed` (BAAI/bge-small-en) — no API key needed | Swap to OpenAI embeddings in `services/embeddings.py` if you prefer |
| Language model | Calls an OpenAI-compatible API if `OPENAI_API_KEY` is set; otherwise falls back to a deterministic `MockLLM` so the whole flow still works offline | Set `OPENAI_API_KEY` / `OPENAI_API_BASE` in `.env` |
| Bhashini translation | Not called automatically; UI has an English/Hindi label toggle only | Call Bhashini/IndicTrans2 from the frontend or a `/api/translate` route |
| Lawyer verification | Bar registration numbers are **self-declared at signup, not verified**. The `verified` flag exists in the data model for exactly this reason but nothing sets it yet. | Integrate a Bar Council of India lookup (or manual admin review) before a lawyer profile can claim cases |

Nothing here silently fabricates a legal conclusion: the risk engine combines
deterministic rule checks with model output, every AI claim needs a
`source_id` or is marked as an inference, and the backend rejects malformed
model output before it reaches the frontend (see `services/llm.py`). Before
any text reaches an external LLM API, `services/redaction.py` strips
Aadhaar-shaped numbers, phone numbers, bank/account-shaped digit runs, and
email addresses (Section 12.1) — local processing (dates, the deterministic
risk engine, retrieval) still runs on the original text, since that never
leaves the server.

The dashboard also has a working evidence locker (upload/download/delete any
file attached to a case), an editable "details we used" tab wired to the
real structured-fact extraction (people, organization, location, amount,
channel, harm, desired outcome, immediate danger — Section 7.3), a banner
when OCR flagged a page as hard to read, and a "Download PDF" button on
generated drafts.

**Lawyer marketplace.** NyayaSetu deliberately does not let the AI issue
legal advice or tell a user whether to pursue a case — that would be
unauthorized practice of law and a real liability/accuracy risk. Instead, a
citizen can opt in (per case, off by default) to share a redacted case
summary with lawyers registered on the platform in that practice area. A
lawyer sees only a title/domain/severity in the browse list; claiming a case
reveals full facts and risk items, and the citizen then sees the lawyer's
profile and contact details. See the "Lawyer verification" row above —
self-declared bar numbers are not yet checked against any real registry.

## Quick start

```bash
cp .env.example .env
# optional: put a real OPENAI_API_KEY / OPENAI_API_BASE in .env for grounded
# generation quality — it runs without one, just with a simpler mock response.

docker compose up --build
```

- API: http://localhost:8000 (docs at http://localhost:8000/docs)
- Web: http://localhost:5173

On first boot the API creates tables and seeds the knowledge base from
`knowledge-base/sources.json` + `seed_chunks.jsonl` automatically. Sign up
for an account on the web app before creating a case — every case is
scoped to your account.

The first voice recording or audio upload will be slow (a few seconds to a
minute) while `faster-whisper` downloads its model weights — after that it
runs fully offline.

## Demo script (matches Section 16 of the spec)

1. Sign up for an account (or log in), pick a language, accept the notice,
   start a new case.
2. Choose "Rental & tenancy", paste in a sample eviction-notice paragraph (or
   upload a PDF), submit.
3. Watch the processing view, then open the dashboard: **What we found / Why
   it matters / What to do next / Important dates**, each item citing a
   source or marked "inference — verify before relying on this."
4. Confirm the extracted deadline, open the draft center, generate an
   unsubmitted response draft.
5. Repeat with the "Cyber fraud" domain and a short incident description to
   show the Urgent/Emergency escalation path (1930 helpline, cybercrime.gov.in).

## Repository layout

See `apps/api` (FastAPI backend), `apps/web` (React + TS frontend),
`knowledge-base` (seed sources), `infra` (Postgres init), `scripts` (seed/eval
utilities).

## Legal note

This is a prototype plan, not legal advice. All legal content shipped with
the app should be reviewed against current official sources before any real
deployment, per the implementation note in the original spec.
