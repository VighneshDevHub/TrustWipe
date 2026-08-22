import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.wipe_record import WipeRecord

SAMPLE_REPORT = {
    "device_serial": "SSD-WD2023-88451",
    "device_model": "WD Blue SN570 512GB",
    "device_type": "NVMe SSD",
    "wipe_method": "NIST 800-88 Purge - Crypto Erase",
    "started_at": "2026-08-17T10:32:01Z",
    "completed_at": "2026-08-17T10:32:05Z",
    "verification_passed": True,
    "operator": "agent_v1_station3",
}


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_submit_wipe_report_creates_signed_certificate(client):
    resp = await client.post("/api/v1/wipes", json=SAMPLE_REPORT)
    assert resp.status_code == 201

    body = resp.json()
    assert body["device_serial"] == SAMPLE_REPORT["device_serial"]
    assert len(body["report_hash"]) == 64
    assert body["signature"]  # non-empty hex signature
    assert body["ledger_sequence_number"] == 1


@pytest.mark.asyncio
async def test_get_certificate_by_id(client):
    create_resp = await client.post("/api/v1/wipes", json=SAMPLE_REPORT)
    cert_id = create_resp.json()["certificate_id"]

    get_resp = await client.get(f"/api/v1/certificates/{cert_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["certificate_id"] == cert_id


@pytest.mark.asyncio
async def test_get_certificate_not_found(client):
    resp = await client.get("/api/v1/certificates/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_verify_genuine_certificate_passes(client):
    create_resp = await client.post("/api/v1/wipes", json=SAMPLE_REPORT)
    cert_id = create_resp.json()["certificate_id"]

    verify_resp = await client.get(f"/api/v1/verify/{cert_id}")
    assert verify_resp.status_code == 200

    body = verify_resp.json()
    assert body["signature_valid"] is True
    assert body["chain_intact"] is True
    assert body["overall_verified"] is True


@pytest.mark.asyncio
async def test_verify_detects_tampered_certificate(client):
    """The 'demo moment' test: create a valid cert, verify it's green,
    directly tamper with the stored row (simulating a rogue DB edit),
    then verify again and confirm it now fails."""
    create_resp = await client.post("/api/v1/wipes", json=SAMPLE_REPORT)
    cert_id = create_resp.json()["certificate_id"]

    verify_resp = await client.get(f"/api/v1/verify/{cert_id}")
    assert verify_resp.json()["overall_verified"] is True

    # Directly tamper with the DB row, bypassing the API entirely
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WipeRecord).where(WipeRecord.certificate_id == cert_id)
        )
        record = result.scalar_one()
        record.verification_passed = False  # flip a fact after the fact
        await db.commit()

    verify_resp_after = await client.get(f"/api/v1/verify/{cert_id}")
    body = verify_resp_after.json()
    assert body["signature_valid"] is False
    assert body["overall_verified"] is False
