from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.wipe_record import LedgerEntry, WipeRecord
from app.schemas.wipe import CertificateOut

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get("/{certificate_id}", response_model=CertificateOut)
async def get_certificate(
    certificate_id: str, db: AsyncSession = Depends(get_db)
) -> CertificateOut:
    result = await db.execute(
        select(WipeRecord, LedgerEntry)
        .join(LedgerEntry, LedgerEntry.wipe_record_id == WipeRecord.id)
        .where(WipeRecord.certificate_id == certificate_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Certificate not found")

    wipe_record, ledger_entry = row
    return CertificateOut(
        certificate_id=wipe_record.certificate_id,
        device_serial=wipe_record.device_serial,
        device_model=wipe_record.device_model,
        device_type=wipe_record.device_type,
        wipe_method=wipe_record.wipe_method,
        started_at=wipe_record.started_at,
        completed_at=wipe_record.completed_at,
        verification_passed=wipe_record.verification_passed,
        operator=wipe_record.operator,
        report_hash=wipe_record.report_hash,
        signature=wipe_record.signature,
        ledger_sequence_number=ledger_entry.sequence_number,
        created_at=wipe_record.created_at,
    )
