from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_signing_keys
from app.core.crypto import verify_signature
from app.models.wipe_record import LedgerEntry, WipeRecord
from app.schemas.wipe import VerificationResult
from app.services import ledger_service

router = APIRouter(prefix="/verify", tags=["verify"])


@router.get("/{certificate_id}", response_model=VerificationResult)
async def verify_certificate(
    certificate_id: str,
    db: AsyncSession = Depends(get_db),
    signing_keys: tuple[str, str] = Depends(get_signing_keys),
) -> VerificationResult:
    """The core trust check. Re-derives the signable payload from what's
    CURRENTLY stored in the DB and checks it against the stored signature
    — if anyone edited the row directly, this fails. Also re-verifies the
    ledger hash chain up to this record's position, so tampering with any
    earlier record is caught too, not just this one."""
    _private_key_pem, public_key_pem = signing_keys

    result = await db.execute(
        select(WipeRecord, LedgerEntry)
        .join(LedgerEntry, LedgerEntry.wipe_record_id == WipeRecord.id)
        .where(WipeRecord.certificate_id == certificate_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Certificate not found")

    wipe_record, ledger_entry = row

    signature_valid = verify_signature(
        wipe_record.to_signable_dict(), wipe_record.signature, public_key_pem
    )

    chain_result = await ledger_service.verify_chain_integrity(
        db, up_to_sequence=ledger_entry.sequence_number
    )

    overall = signature_valid and chain_result.valid

    if overall:
        detail = "Certificate is authentic and has not been tampered with."
    elif not signature_valid:
        detail = "Signature mismatch — this record's data does not match its original signature."
    else:
        detail = (
            f"Ledger chain broken at sequence {chain_result.broken_at_sequence}: "
            f"{chain_result.reason}"
        )

    return VerificationResult(
        certificate_id=certificate_id,
        signature_valid=signature_valid,
        chain_intact=chain_result.valid,
        overall_verified=overall,
        detail=detail,
    )
