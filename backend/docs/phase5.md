# Phase 5 — Auth + Recycler Dashboard

## What this phase delivers

- Backend: JWT-based auth (`/auth/register`, `/auth/login`) and a
  protected `GET /certificates` list endpoint
- Frontend: `/login` page and a `/dashboard` page showing every device
  processed, with status badges, a link to each PDF, and CSV export

This is the piece that turns TrustWipe from "a trust mechanism" into "a
tool an actual ITAD company would use daily" — the business/compliance
story your pitch needs.

## Files added/changed

```
backend/
├── app/
│   ├── models/user.py              # NEW — User model
│   ├── core/security.py            # NEW — bcrypt hashing + JWT issue/verify
│   ├── schemas/auth.py              # NEW — register/login/token schemas
│   ├── api/v1/auth.py               # NEW — /auth/register, /auth/login
│   ├── api/deps.py                  # CHANGED — added get_current_user
│   ├── api/v1/certificates.py       # CHANGED — added protected GET /certificates (list)
│   └── main.py                      # CHANGED — wired in auth router
└── tests/
    └── test_auth.py                 # NEW — 9 tests covering register/login/protection

frontend/
├── src/
│   ├── lib/auth.ts                  # NEW — token storage, login/register/logout
│   ├── lib/api.ts                   # CHANGED — added listCertificates() with auth header
│   ├── app/login/page.tsx           # NEW
│   └── app/dashboard/page.tsx       # NEW
```

## Commands to run it yourself

```bash
cd backend
pip install -r requirements.txt   # now includes pinned bcrypt==4.0.1, python-jose
pytest -v                          # 27 passed
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run build      # confirms no type errors
npm run dev         # http://localhost:3000
```

## How to test it manually

1. Register: `POST /api/v1/auth/register` with `{"email": "...", "password": "..."}` (via Swagger `/docs`, or the frontend has no signup form yet — see note below)
2. Go to `http://localhost:3000/login`, sign in with those credentials
3. You're redirected to `/dashboard` — initially empty
4. Run the Phase 2 wipe agent (or submit via Swagger) a few times
5. Refresh the dashboard — devices appear, newest first, with status
   badges and PDF links
6. Click "Export CSV" — downloads a real CSV of everything shown
7. Try opening `http://localhost:3000/dashboard` in an incognito window
   (no token) — redirects straight to `/login`, confirming the guard works

## What we tested

| Test | What it proves |
|---|---|
| `test_register_creates_user` / `test_register_rejects_duplicate_email` | Registration works and enforces unique emails |
| `test_login_succeeds_with_correct_password` / `test_login_fails_with_wrong_password` / `test_login_fails_for_unknown_email` | Login only succeeds with correct credentials; wrong password and unknown email both return the same generic 401 (no account-enumeration leak) |
| `test_list_certificates_requires_auth` / `test_list_certificates_rejects_garbage_token` | The dashboard endpoint is genuinely protected — no token or a garbage token both fail with 401 |
| `test_list_certificates_succeeds_with_valid_token` / `test_list_certificates_orders_newest_first` | A real logged-in user sees the correct devices, newest-first |

All 27 backend tests pass (18 from Phases 1+3, 9 new for auth). Also
ran a full live integration: registered a real account, logged in,
confirmed `401` without a token, submitted 3 wipe reports, and confirmed
the dashboard endpoint returned all 3 in the right order with a real JWT.

## Two real dependency bugs we hit and fixed (good judge Q&A material)

1. **Reserved TLD in test emails.** Using `.test` addresses (a
   convention some devs assume is always "safe" for testing) got
   rejected by `email-validator`, which correctly treats `.test` as a
   reserved, non-deliverable TLD per RFC 2606. Switched test fixtures to
   `.example` instead (also reserved, but accepted by the validator).
2. **passlib + modern bcrypt incompatibility.** `passlib`'s bcrypt
   backend runs an internal self-test on import that itself breaks
   against `bcrypt>=4.1`'s stricter 72-byte password handling, raising a
   `ValueError` before any of *our* code even runs. Pinned
   `bcrypt==4.0.1` in `requirements.txt` with a comment explaining why —
   this is a known, open compatibility gap in the passlib project, not
   something specific to this app.

Both were caught immediately by the test suite rather than silently
producing broken logins in a demo.

## Production notes

- **No self-serve signup UI yet** — registration currently requires
  hitting the API directly (Swagger or curl). A signup form is a
  straightforward Phase 6 addition, intentionally deprioritized since it
  doesn't affect the trust-engine correctness that matters most for
  judging.
- **Token storage**: the frontend stores the JWT in `localStorage`. Fine
  for an MVP; a hardened production version would use an httpOnly cookie
  instead to reduce XSS exposure.
- **Multi-tenancy**: every logged-in user currently sees every device
  ever wiped, with no per-organization scoping. Real ITAD software would
  need a `organization_id` on both `User` and `WipeRecord` — noted as a
  clear, well-understood extension rather than a design flaw specific to
  this MVP.
- **JWT secret**: `JWT_SECRET_KEY` defaults to a placeholder in
  `.env.example`. Must be replaced with a real random secret before any
  non-local deployment — same rule as the ECDSA signing key.

## Next: Phase 6

Docker + docker-compose to tie backend, frontend, and (optionally)
Postgres into a single `docker-compose up` — the final piece that makes
this a genuine one-command resume deliverable. Say "next" when ready.
