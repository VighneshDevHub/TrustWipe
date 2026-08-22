import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_signing_keys
from app.core.crypto import sign_payload
from app.models.wipe_record import WipeRecord
from app.schemas.wipe import CertificateOut, WipeReportIn
from app.services import ledger_service

router = APIRouter(prefix="/wipes", tags=["wipes"])

@router.post("", response_model=CertificateOut, status_code=201)
async def submit_wipe_report(
    report: WipeReportIn,
    db: AsyncSession = Depends(get_db),
    signing_keys: tuple[str, str] = Depends(get_signing_keys),
) -> CertificateOut:
    """Receive a wipe report from an agent, sign it, and append it to the
    tamper-evident ledger. This is the only way a WipeRecord gets created —
    there is deliberately no update/delete endpoint for wipe_records."""
    private_key_pem, _public_key_pem = signing_keys

    # IMPORTANT: certificate_id must be generated explicitly here, not left
    # to the column's default=. SQLAlchemy python-side column defaults only
    # fire at flush time — if we signed before that, certificate_id would
    # be None in the signed payload but populated by the time anyone
    # verifies it later, making every signature look "tampered" even
    # though nothing was actually altered.
    wipe_record = WipeRecord(
        certificate_id=str(uuid.uuid4()),
        device_serial=report.device_serial,
        device_model=report.device_model,
        device_type=report.device_type,
        wipe_method=report.wipe_method,
        started_at=report.started_at,
        completed_at=report.completed_at,
        verification_passed=report.verification_passed,
        operator=report.operator,
        report_hash="",  # filled in below once we have the signable dict
        signature="",
    )

    # Hash + sign the canonical form of the record's trusted fields
    report_hash, signature = sign_payload(
        wipe_record.to_signable_dict(), private_key_pem
    )
    wipe_record.report_hash = report_hash
    wipe_record.signature = signature

    db.add(wipe_record)
    await db.flush()  # assigns wipe_record.id without committing yet

    ledger_entry = await ledger_service.append_to_ledger(db, wipe_record)
    await db.commit()
    await db.refresh(wipe_record)
    await db.refresh(ledger_entry)

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
