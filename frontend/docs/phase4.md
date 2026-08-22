# Phase 4 — Verification Portal

## What this phase delivers

A Next.js frontend with two pages:
- `/` — a landing page where someone can manually type in a certificate ID
- `/verify/[certId]` — the actual QR-code destination: fetches the
  certificate and its live verification status, and renders a clear
  green ✅ / red ❌ result plus device details and a PDF download link

This is the page a buyer or auditor actually lands on.

## Directory structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # root layout, global metadata
│   │   ├── globals.css             # Tailwind directives
│   │   ├── page.tsx                # landing page — manual cert ID entry
│   │   └── verify/[certId]/
│   │       └── page.tsx            # the verification page (QR destination)
│   ├── components/
│   │   └── VerificationResult.tsx  # green/red banner + device details cards
│   └── lib/
│       ├── api.ts                  # fetch wrappers for backend endpoints
│       └── types.ts                # TS types mirroring backend Pydantic schemas
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── next.config.js
└── .env.local.example
```

## Commands to run it yourself

```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL if backend isn't on :8000

npm run build     # production build — confirms no type/lint errors
npm run dev        # dev server with hot reload, http://localhost:3000
```

Make sure the Phase 1/3 backend is running on port 8000 first (`cd
../backend && uvicorn app.main:app --port 8000`), since the frontend has
nothing to show without it.

## How to test it manually — this is your actual demo script now

1. Submit a wipe report (via Swagger `/docs`, or run the Phase 2 wipe
   agent against the backend) — copy the `certificate_id`
2. Open `http://localhost:3000/verify/{certificate_id}` in a browser
3. You should see a **green "VERIFIED"** banner with device details and a
   "Download Certificate PDF" button
4. **The tamper demo, now with a real UI**: open the backend's SQLite
   file (`backend/trustwipe.db`) in DB Browser for SQLite, flip
   `verification_passed` on that row, save
5. Refresh the browser tab — banner flips to **red "INVALID / TAMPERED"**
   with the specific reason shown

This replaces the curl-based demo from earlier phases with an actual
page you can show judges live on a projector — much stronger visually.

## What we verified (not unit tests this time — full stack integration)

Rather than component-level tests (reasonable to skip given hackathon
time constraints — this is presentation-layer code with no business
logic of its own), we validated the whole stack together:

| Check | Result |
|---|---|
| `npm run build` | Compiles with zero type errors, zero lint errors |
| Backend + frontend running together | Backend health check `200`, frontend `/verify/{id}` route `200` |
| Full round trip | Submitted a real wipe report → frontend route resolves → backend verify returns `overall_verified: true` |

If you want actual component tests for a resume-polish pass later,
Playwright is a good fit (matches Next.js well) — noted as a Phase 6
extension rather than built now, so time went into the trust-engine
correctness that actually matters for judging.

## A dependency security fix worth mentioning

`npm install` initially pulled in `next@14.2.15`, which npm itself
flagged as having a known security vulnerability. Bumped to the latest
patched `14.2.x` release (`14.2.35`) and `postcss` to `8.5.26` before
writing any application code on top of it — a small thing, but "I check
`npm audit` before building on a dependency" is a good habit to mention
if a judge asks about your process. One residual moderate-severity
advisory remains, bundled *inside* Next's own internal build tooling
(not a package our code touches directly) — it concerns Next's Image
Optimizer's `remotePatterns` config, which this app doesn't use at all,
so it's a documented, accepted low-risk gap rather than something
silently ignored.

## Production notes

- **CORS**: Phase 1's backend currently allows all origins in dev
  (`allow_origins=["*"]`). Before real deployment, set `PUBLIC_BASE_URL`
  in the backend `.env` to your actual frontend domain so CORS is locked
  down to only that origin.
- **Server-side rendering**: the verify page is currently a client
  component (`"use client"`) for simplicity around loading states. A
  production polish pass could fetch server-side for faster first paint
  and better SEO/link-preview behavior — noted as a nice-to-have, not
  required for correctness.
- **Styling**: Tailwind utility classes only, no design system — fine for
  MVP; a design pass (real typography, spacing rhythm, TrustWipe branding)
  is a good "if we had one more day" pitch line.

## Next: Phase 5

Auth (JWT) + the recycler dashboard — a login-gated page showing a table
of every device wiped, with export for compliance reporting. This is the
piece that shows business viability for an actual ITAD company, not just
the trust mechanism. Say "next" when ready.
