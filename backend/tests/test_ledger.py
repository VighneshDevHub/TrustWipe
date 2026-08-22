from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.wipe_record import LedgerEntry, WipeRecord
from app.services import ledger_service


async def _make_wipe_record(db, serial: str) -> WipeRecord:
    wr = WipeRecord(
        device_serial=serial,
        device_model="Test SSD",
        device_type="NVMe",
        wipe_method="NIST 800-88 Purge",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        verification_passed=True,
        operator="pytest",
        report_hash=f"hash-for-{serial}",
        signature="dummy-signature",
    )
    db.add(wr)
    await db.flush()
    return wr


@pytest.mark.asyncio
async def test_chain_starts_from_genesis():
    async with AsyncSessionLocal() as db:
        wr = await _make_wipe_record(db, "SN-001")
        entry = await ledger_service.append_to_ledger(db, wr)
        await db.commit()

        assert entry.sequence_number == 1
        assert entry.previous_hash == ledger_service.GENESIS_HASH


@pytest.mark.asyncio
async def test_chain_links_sequential_entries():
    async with AsyncSessionLocal() as db:
        wr1 = await _make_wipe_record(db, "SN-001")
        e1 = await ledger_service.append_to_ledger(db, wr1)
        await db.commit()

        wr2 = await _make_wipe_record(db, "SN-002")
        e2 = await ledger_service.append_to_ledger(db, wr2)
        await db.commit()

        assert e2.previous_hash == e1.entry_hash
        assert e2.sequence_number == 2


@pytest.mark.asyncio
async def test_verify_chain_integrity_passes_on_untouched_chain():
    async with AsyncSessionLocal() as db:
        for i in range(3):
            wr = await _make_wipe_record(db, f"SN-{i}")
            await ledger_service.append_to_ledger(db, wr)
            await db.commit()

        result = await ledger_service.verify_chain_integrity(db)
        assert result.valid is True
        assert result.total_entries == 3


@pytest.mark.asyncio
async def test_verify_chain_integrity_detects_tampering():
    """This is the test that proves the core value proposition: if someone
    edits a historical ledger entry's stored hash directly in the DB, the
    chain must be detected as broken from that point forward."""
    async with AsyncSessionLocal() as db:
        for i in range(3):
            wr = await _make_wipe_record(db, f"SN-{i}")
            await ledger_service.append_to_ledger(db, wr)
            await db.commit()

        # Simulate a rogue edit directly on entry #1's report_hash
        result = await db.execute(
            select(LedgerEntry).where(LedgerEntry.sequence_number == 1)
        )
        entry_one = result.scalar_one()
        entry_one.report_hash = "0" * 64  # tampered value
        await db.commit()

        result = await ledger_service.verify_chain_integrity(db)
        assert result.valid is False
        assert result.broken_at_sequence == 1
