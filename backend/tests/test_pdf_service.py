from app.services.pdf_service import generate_certificate_pdf

SAMPLE_CERTIFICATE = {
    "certificate_id": "c-test-1234",
    "device_serial": "SSD-WD2023-88451",
    "device_model": "WD Blue SN570 512GB",
    "device_type": "NVMe SSD",
    "wipe_method": "NIST 800-88 Purge - Crypto Erase",
    "started_at": "2026-08-17T10:32:01+00:00",
    "completed_at": "2026-08-17T10:32:05+00:00",
    "verification_passed": True,
    "operator": "demo-operator",
    "report_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85",
    "signature": "3045022100f9a8b7c6d5e4f3a2b1" + "a" * 100,
    "ledger_sequence_number": 1,
    "created_at": "2026-08-17T10:32:06+00:00",
}


def test_generate_certificate_pdf_returns_valid_pdf_bytes():
    pdf_bytes = generate_certificate_pdf(SAMPLE_CERTIFICATE)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000  # sanity check it's not an empty/broken doc


def test_generate_certificate_pdf_handles_long_signature_without_crashing():
    cert = dict(SAMPLE_CERTIFICATE)
    cert["signature"] = "ab" * 500  # unusually long, must not blow up layout
    pdf_bytes = generate_certificate_pdf(cert)
    assert pdf_bytes.startswith(b"%PDF")
