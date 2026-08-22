"""
Tamper-evident ledger service.

Every signed wipe record gets one ledger entry. Each entry's `entry_hash`
is sha256(previous_entry_hash + this_record's_report_hash) — so entry N
can only be correctly recomputed if every entry before it is unchanged.

This gives us tamper-EVIDENCE (not prevention): nobody can quietly edit
old records, because doing so breaks the chain for every subsequent
entry, and re-verification will show exactly where the chain broke.

GENESIS_HASH is a fixed, publicly known starting value (64 zeros) so the
very first ledger entry has something deterministic to chain from.
"""
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import sha256_hex
from app.models.wipe_record import LedgerEntry, WipeRecord

GENESIS_HASH = "0" * 64


@dataclass
class ChainVerificationResult:
    valid: bool
    total_entries: int
    broken_at_sequence: int | None = None
    reason: str | None = None


async def get_latest_entry(db: AsyncSession) -> LedgerEntry | None:
    result = await db.execute(
        select(LedgerEntry).order_by(LedgerEntry.sequence_number.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def append_to_ledger(db: AsyncSession, wipe_record: WipeRecord) -> LedgerEntry:
    """Append a new entry to the chain for the given (already-signed)
    wipe record. Must be called inside the same transaction that creates
    the wipe_record, so the two are committed atomically."""
    latest = await get_latest_entry(db)
    previous_hash = latest.entry_hash if latest else GENESIS_HASH
    next_sequence = (latest.sequence_number + 1) if latest else 1

    entry_hash = sha256_hex((previous_hash + wipe_record.report_hash).encode())

    entry = LedgerEntry(
        sequence_number=next_sequence,
        wipe_record_id=wipe_record.id,
        report_hash=wipe_record.report_hash,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )
    db.add(entry)
    return entry


async def verify_chain_integrity(
    db: AsyncSession, up_to_sequence: int | None = None
) -> ChainVerificationResult:
    """Recompute the entire hash chain from genesis and compare against
    what's stored. Used by the verification endpoint and by a periodic
    integrity-check job in production. O(n) in the number of ledger
    entries — fine for demo/MVP scale; production should cache the last
    verified sequence number and only re-check the delta."""
    query = select(LedgerEntry).order_by(LedgerEntry.sequence_number.asc())
    if up_to_sequence is not None:
        query = query.where(LedgerEntry.sequence_number <= up_to_sequence)

    result = await db.execute(query)
    entries = result.scalars().all()

    expected_previous = GENESIS_HASH
    for entry in entries:
        if entry.previous_hash != expected_previous:
            return ChainVerificationResult(
                valid=False,
                total_entries=len(entries),
                broken_at_sequence=entry.sequence_number,
                reason="previous_hash does not match prior entry's stored hash",
            )
        recomputed = sha256_hex((entry.previous_hash + entry.report_hash).encode())
        if recomputed != entry.entry_hash:
            return ChainVerificationResult(
                valid=False,
                total_entries=len(entries),
                broken_at_sequence=entry.sequence_number,
                reason="entry_hash does not match recomputed hash — record was altered",
            )
        expected_previous = entry.entry_hash

    return ChainVerificationResult(valid=True, total_entries=len(entries))


async def get_ledger_length(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(LedgerEntry))
    return result.scalar_one()
