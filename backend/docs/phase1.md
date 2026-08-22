# Phase 1 — Backend Trust Engine

## What this phase delivers

A working FastAPI service that:
1. Receives a wipe report (`POST /api/v1/wipes`)
2. Signs it with ECDSA (P-256) so its authenticity is cryptographically provable
3. Appends it to a tamper-evident hash-chain ledger
4. Lets anyone fetch the certificate (`GET /api/v1/certificates/{id}`)
5. Lets anyone independently re-verify it (`GET /api/v1/verify/{id}`) — this is
   the endpoint that detects tampering

This is the trust root every other phase depends on. Nothing here talks to a
real disk yet — that's Phase 2.

## Directory structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app, CORS, router wiring
│   ├── api/
│   │   ├── deps.py                # DB session + signing key DI
│   │   └── v1/
│   │       ├── wipes.py           # POST /wipes
│   │       ├── certificates.py    # GET /certificates/{id}
│   │       └── verify.py          # GET /verify/{id}
│   ├── core/
│   │   ├── config.py              # env-based settings
│   │   └── crypto.py              # ECDSA sign/verify, canonical JSON, hashing
│   ├── models/
│   │   └── wipe_record.py         # WipeRecord + LedgerEntry (SQLAlchemy)
│   ├── schemas/
│   │   └── wipe.py                # Pydantic request/response models
│   ├── services/
│   │   └── ledger_service.py      # hash-chain append + integrity check
│   └── db/
│       └── session.py             # async engine + session factory
├── tests/
│   ├── conftest.py
│   ├── test_crypto.py             # signing correctness
│   ├── test_ledger.py             # hash-chain correctness + tamper detection
│   └── test_api.py                # end-to-end incl. tamper-detection demo
├── requirements.txt
├── .env.example
└── pytest.ini
```

## Commands to run it yourself

```bash
cd backend
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env

# Run the test suite
pytest -v

# Run the server
uvicorn app.main:app --reload --port 8000
# Swagger docs: http://localhost:8000/docs
```

## How to test it manually (no code needed)

1. Open `http://localhost:8000/docs` (auto-generated Swagger UI)
2. Expand `POST /api/v1/wipes`, click "Try it out", use this example body:
   ```json
   {
     "device_serial": "SSD-DEMO-001",
     "device_model": "Samsung 970 EVO",
     "device_type": "NVMe SSD",
     "wipe_method": "NIST 800-88 Purge - Crypto Erase",
     "started_at": "2026-08-22T10:00:00Z",
     "completed_at": "2026-08-22T10:00:05Z",
     "verification_passed": true,
     "operator": "demo-operator"
   }
   ```
3. Copy the `certificate_id` from the response
4. Call `GET /api/v1/verify/{certificate_id}` → should show `overall_verified: true`
5. **The tamper demo**: open `trustwipe.db` with any SQLite browser (e.g. "DB
   Browser for SQLite"), find the row in `wipe_records`, flip
   `verification_passed` from 1 to 0, save
6. Call `GET /api/v1/verify/{certificate_id}` again → now shows
   `overall_verified: false` with a clear reason

This is the entire hackathon demo moment, and it's already fully working.

## What we tested (and why each test matters)

| Test file | What it proves |
|---|---|
| `test_crypto.py` | A signature verifies against the correct payload + public key, and fails against any altered payload, wrong key, or garbage signature |
| `test_ledger.py` | The hash chain links correctly entry-to-entry, and — critically — `verify_chain_integrity` detects exactly where a chain was broken if any historical entry is altered |
| `test_api.py` | Full HTTP round trip: submit → certificate created → fetch → verify green → tamper directly in DB → verify red |

All 14 tests pass. Run `pytest -v` to reproduce.

## A real bug we hit and fixed (worth knowing for your judge Q&A)

Two issues surfaced during testing that are worth explaining if asked "how do
you know this actually works":

1. **SQLite drops timezone info on round-trip.** A datetime saved as
   UTC-aware comes back naive after a reload, which would make a freshly
   signed certificate immediately fail its own verification. Fixed by
   normalizing timestamps to UTC ISO strings in `to_signable_dict()`,
   treating a naive datetime as already-UTC.
2. **SQLAlchemy column defaults (`default=uuid4`) don't fire until flush.**
   We were signing the record before its `certificate_id` had been
   generated, so the signed payload had `certificate_id: null` while the
   stored/returned record had a real UUID — a mismatch that looked exactly
   like tampering. Fixed by generating the UUID explicitly before signing.

Both were caught by the test suite before ever reaching a demo — this is
the value of testing each phase before moving on.

## Production notes (for your resume/README, and for judges who ask "is this real")

- **Signing key persistence**: right now, if no `SIGNING_PRIVATE_KEY_PEM` is
  set, the app generates an ephemeral keypair at startup — fine for a demo,
  but it means certificates signed before a restart won't verify after one.
  Production must set a stable key via a secrets manager.
- **Database**: swap `DATABASE_URL` to a `postgresql+asyncpg://...` URL —
  the code is already async-SQLAlchemy and dialect-agnostic. No code changes
  needed, only the connection string and installing `asyncpg` (already in
  requirements.txt).
- **Migrations**: Phase 1 uses `Base.metadata.create_all()` for fast
  iteration. Before shipping, run `alembic init alembic` and generate a real
  migration so schema changes are tracked and reversible.
- **Immutability**: `wipe_records` and `ledger_entries` are never updated or
  deleted by application code — there is deliberately no PUT/PATCH/DELETE
  endpoint. This is a design invariant, not an accident.

## Next: Phase 2

The Wipe Agent — a small Python program that runs on the actual device,
detects the drive type, performs (or simulates) the wipe, and calls
`POST /api/v1/wipes` with a real report. Say "go" or "next" when ready.
