# Phase 3 — Certificate PDF + QR Code

## What this phase delivers

A new endpoint, `GET /api/v1/certificates/{certificate_id}/pdf`, that
renders the signed wipe record as a downloadable PDF containing:
- All device and wipe details
- The report hash and (truncated) digital signature, for anyone who wants
  to manually inspect it
- An embedded QR code linking to the live verification endpoint

This is the artifact a device owner would actually hand to a buyer —
everything before this phase lived only as JSON.

## Files added/changed

```
backend/
├── app/
│   ├── services/
│   │   └── pdf_service.py         # NEW — builds the PDF + QR code
│   └── api/v1/
│       └── certificates.py        # CHANGED — added /pdf route
└── tests/
    ├── test_pdf_service.py        # NEW — PDF generation unit tests
    └── test_api.py                # CHANGED — added PDF endpoint tests
```

## Commands to run it yourself

```bash
cd backend
pip install -r requirements.txt   # now includes qrcode[pil] and reportlab
pytest -v                          # 18 passed
uvicorn app.main:app --reload --port 8000
```

## How to test it manually

1. Submit a wipe report via `POST /api/v1/wipes` (Swagger UI at `/docs`,
   or reuse the same JSON body from Phase 1's docs)
2. Copy the `certificate_id` from the response
3. Open in a browser: `http://localhost:8000/api/v1/certificates/{certificate_id}/pdf`
   — the PDF renders directly in-browser (or downloads, depending on
   browser settings)
4. Scan the QR code on the PDF with your phone — it should open
   `{PUBLIC_BASE_URL}/verify/{certificate_id}` (this URL will 404 until
   Phase 4 builds the actual verification portal page — that's expected
   right now, the QR code itself is correctly generated and pointing at
   the right place)

A sample PDF generated from a real API call is included alongside this
delivery so you can see the actual output without running anything.

## Design decision worth explaining to judges

**The PDF is a convenience artifact, not the source of trust.** Anyone
could, in principle, edit a PDF's text. That's exactly why the PDF's
value is the QR code, not the printed fields — the QR always points back
to a live re-verification against the signed database record. If someone
edited the PDF text to say "verification passed: YES" when the real
record says otherwise, scanning the QR still shows the true, current,
cryptographically-checked state. This is a good one-liner for your pitch:
*"Don't trust the paper — trust what it points to."*

## What we tested

| Test | What it proves |
|---|---|
| `test_generate_certificate_pdf_returns_valid_pdf_bytes` | Output is a real, valid PDF (`%PDF` header, non-trivial size) |
| `test_generate_certificate_pdf_handles_long_signature_without_crashing` | Layout doesn't break on unusually long signature/hash values |
| `test_get_certificate_pdf_returns_valid_pdf` | Full HTTP round trip: submit wipe → fetch PDF → confirm correct content-type and valid PDF bytes |
| `test_get_certificate_pdf_404_for_unknown_id` | Requesting a PDF for a nonexistent certificate fails cleanly instead of crashing |

All 18 backend tests pass (10 from Phase 1 + 4 new PDF-specific ones + 4
existing API tests still green).

## Production notes

- **PUBLIC_BASE_URL**: currently defaults to `http://localhost:3000` in
  `.env`. Before a real deployment, set this to your actual public
  domain (e.g. `https://verify.trustwipe.app`) so QR codes on printed
  certificates resolve correctly outside your dev machine.
- **PDF styling**: current layout is intentionally plain/functional —
  fine for a hackathon demo. A polish pass (logo, better typography,
  letterhead) is a good "if we had one more day" talking point, not a
  blocker.
- **Caching**: PDFs are regenerated fresh on every request rather than
  stored. For a high-volume production deployment, consider caching
  generated PDFs (e.g. in object storage) keyed by certificate_id, since
  the underlying record never changes after creation.

## Next: Phase 4

The verification portal — the actual page the QR code should point to,
where anyone can scan/enter a certificate ID and see a live green/red
result. This is also where we'll do the full live tamper demo through a
real UI instead of curl. Say "next" when ready.
