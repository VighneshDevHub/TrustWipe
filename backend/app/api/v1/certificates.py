from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.wipe_record import LedgerEntry, WipeRecord
from app.schemas.wipe import CertificateOut
from app.services.pdf_service import generate_certificate_pdf

router = APIRouter(prefix="/certificates", tags=["certificates"])


async def _fetch_certificate(certificate_id: str, db: AsyncSession) -> CertificateOut:
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


@router.get("", response_model=list[CertificateOut])
async def list_certificates(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0,
) -> list[CertificateOut]:
    """Powers the recycler dashboard table. Protected — requires a valid
    JWT, since this exposes the full history of every device processed."""
    result = await db.execute(
        select(WipeRecord, LedgerEntry)
        .join(LedgerEntry, LedgerEntry.wipe_record_id == WipeRecord.id)
        .order_by(desc(LedgerEntry.sequence_number))
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()
    return [
        CertificateOut(
            certificate_id=wr.certificate_id,
            device_serial=wr.device_serial,
            device_model=wr.device_model,
            device_type=wr.device_type,
            wipe_method=wr.wipe_method,
            started_at=wr.started_at,
            completed_at=wr.completed_at,
            verification_passed=wr.verification_passed,
            operator=wr.operator,
            report_hash=wr.report_hash,
            signature=wr.signature,
            ledger_sequence_number=le.sequence_number,
            created_at=wr.created_at,
        )
        for wr, le in rows
    ]


@router.get("/{certificate_id}", response_model=CertificateOut)
async def get_certificate(
    certificate_id: str, db: AsyncSession = Depends(get_db)
) -> CertificateOut:
    return await _fetch_certificate(certificate_id, db)


@router.get("/{certificate_id}/pdf")
async def get_certificate_pdf(
    certificate_id: str, db: AsyncSession = Depends(get_db)
) -> Response:
    """Renders the certificate as a downloadable PDF with an embedded QR
    code linking to the live verification endpoint. Regenerated fresh on
    every request from the current DB state — if the underlying record
    were ever tampered with, the PDF would reflect the tampered data too,
    but the QR code's live verification would still catch it, which is
    exactly the point: the PDF is a convenience, not the source of trust.
    """
    certificate = await _fetch_certificate(certificate_id, db)
    pdf_bytes = generate_certificate_pdf(certificate.model_dump(mode="json"))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="certificate_{certificate_id}.pdf"'
        },
    )

