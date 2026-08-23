# TrustWipe

**Secure, cryptographically verifiable data erasure for trustworthy IT asset recycling.**

TrustWipe solves a specific trust gap: it's easy to wipe a drive, but hard
to *prove* it was wiped — in a way a buyer, auditor, or regulator can
verify without just taking your word for it. TrustWipe signs every wipe
with ECDSA, chains records into a tamper-evident ledger, and gives anyone
a QR code that re-verifies the record live, on demand.

Built for Problem Statement #5 — *Secure Data Wiping for Trustworthy IT
Asset Recycling*.

## What it does

1. A **wipe agent** detects a device, picks the right NIST SP 800-88
   method (Clear / Purge / Crypto Erase) based on device type, wipes it,
   and verifies the wipe with random-offset read-back sampling.
2. A **backend** signs the resulting report with ECDSA (P-256), appends
   it to an append-only hash-chain ledger, and issues a certificate.
3. A **verification portal** lets anyone scan a QR code or enter a
   certificate ID and get a live green ✅ / red ❌ result — re-derived
   from the current database state every time, not cached.
4. A **recycler dashboard** (JWT-authenticated) gives an ITAD company a
   table of every device processed, with PDF certificates and CSV export.
5. Everything runs via **one `docker compose up`** — Postgres, backend,
   and frontend together.

## Why this is hard (and the actual point of the project)

Anyone can write a script that overwrites a disk. The interesting
problem is **proof that survives scrutiny**:
- The certificate is signed, so editing it invalidates the signature.
- Records are hash-chained, so editing history breaks every entry after it.
- Verification is always re-derived live — the PDF is a convenience, the
  QR code's live check is the actual source of trust.

This is demonstrated with a real, working tamper-detection flow: verify
a genuine certificate (green), edit the underlying record directly in
the database, verify again (red, with the specific reason shown).

## Project structure

```
trustwipe/
├── backend/       # FastAPI trust engine — signing, ledger, auth, PDF, API
├── wipe-agent/    # Python CLI — device detection, wipe execution, reporting
├── frontend/      # Next.js — verification portal + recycler dashboard
├── docker-compose.yml
└── docs/          # Phase-by-phase build documentation
```

Each subfolder has its own `docs/phaseN.md` covering what was built, how
to run it, how it was tested, and what a production hardening pass would
add. Read those for full detail — this README is the map.

## Quick start (Docker — recommended)

```bash
cp .env.example .env
# Fill in JWT_SECRET_KEY and SIGNING_PRIVATE_KEY_PEM / SIGNING_PUBLIC_KEY_PEM
# (see .env.example for the exact generation commands)

docker compose up --build
```

- Backend API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Quick start (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
pytest -v                 # 30 passed
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                # http://localhost:3000

# Wipe agent (separate terminal, after backend is running)
cd wipe-agent
pip install -r requirements.txt
pytest -v                  # 14 passed
python -m src.main --target test_volume.img --operator "demo" --api-url http://localhost:8000
```

## Tech stack

| Layer | Technology |
|---|---|
| Wipe agent | Python 3.12, cross-platform device detection |
| Backend | FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, ECDSA (`cryptography`), JWT (`python-jose`), `reportlab` + `qrcode` |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Trust layer | ECDSA P-256 signing, SHA-256 hash-chain ledger |
| Deployment | Docker + docker-compose |

## Test coverage

- Backend: 30 tests (signing correctness, hash-chain integrity and
  tamper detection, full API round trips, auth, PDF generation, config)
- Wipe agent: 14 tests (wipers, detectors, verifier, report schema)
- Frontend: verified via full-stack integration runs against the live
  backend rather than isolated component tests (presentation layer with
  no independent business logic)

Every phase was tested end-to-end against a live server before moving
to the next — see `docs/phaseN.md` in each folder for the specific test
runs and, where relevant, real bugs found and fixed along the way.

## Standards referenced

- **NIST SP 800-88** — Guidelines for Media Sanitization (Clear / Purge / Destroy)
- Regulatory relevance: GDPR "right to erasure," India's E-Waste
  (Management) Rules, R2/e-Stewards ITAD certification requirements

## Known limitations / honest scope notes

- Windows and real hardware detection are architected (interface-based,
  see `wipe-agent/src/detectors/`) but only the safe file-target demo
  path and Linux block-device detection are implemented.
- No multi-tenancy — every dashboard user currently sees every device
  ever processed. A real ITAD deployment needs per-organization scoping.
- Docker Compose setup was validated via YAML syntax checks, a clean
  dependency install, and Postgres-dialect engine construction — but
  not run end-to-end with a live Docker daemon in the environment this
  was built in. Run `docker compose up --build` yourself to confirm.

## License

MIT 
