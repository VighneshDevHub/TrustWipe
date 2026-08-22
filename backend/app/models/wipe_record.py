import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WipeRecord(Base):
    """One row per device wipe. This is the raw, signed record of what
    the wipe agent reported. Immutable once created — never UPDATE this
    row; any correction must be a brand-new record, so the audit trail
    stays honest."""

    __tablename__ = "wipe_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    certificate_id: Mapped[str] = mapped_column(
        String(36), unique=True, default=_uuid, index=True
    )

    # Device identity
    device_serial: Mapped[str] = mapped_column(String(128), index=True)
    device_model: Mapped[str] = mapped_column(String(128))
    device_type: Mapped[str] = mapped_column(String(64))  # HDD / SSD / NVMe / USB

    # Wipe details
    wipe_method: Mapped[str] = mapped_column(String(128))  # e.g. "NIST 800-88 Purge"
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    verification_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    operator: Mapped[str] = mapped_column(String(128))

    # Trust layer
    report_hash: Mapped[str] = mapped_column(String(64))  # sha256 hex of canonical report
    signature: Mapped[str] = mapped_column(Text)  # ECDSA signature, hex-encoded

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    ledger_entry: Mapped["LedgerEntry"] = relationship(
        back_populates="wipe_record", uselist=False
    )

    @staticmethod
    def _normalize_dt(dt: datetime) -> str:
        """Normalize to a UTC ISO string regardless of tzinfo presence.

        SQLite (unlike Postgres) does not preserve tzinfo across a
        round-trip: a datetime saved as UTC-aware comes back naive on
        reload. If we called .isoformat() directly, the string would
        differ before vs. after a DB reload and every signature would
        appear "tampered" even though nothing changed. Treating a naive
        datetime as already-UTC keeps the signable representation stable
        across that round-trip.
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    def to_signable_dict(self) -> dict:
        """The exact set of fields that get hashed + signed. Keep this
        stable — changing it invalidates every previously issued signature."""
        return {
            "certificate_id": self.certificate_id,
            "device_serial": self.device_serial,
            "device_model": self.device_model,
            "device_type": self.device_type,
            "wipe_method": self.wipe_method,
            "started_at": self._normalize_dt(self.started_at),
            "completed_at": self._normalize_dt(self.completed_at),
            "verification_passed": self.verification_passed,
            "operator": self.operator,
        }


class LedgerEntry(Base):
    """Append-only hash chain. Each entry embeds the hash of the entry
    before it (`previous_hash`), so altering any historical record breaks
    the chain from that point forward — this is what makes tampering
    detectable, independent of the per-record signature check."""

    __tablename__ = "ledger_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    sequence_number: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    wipe_record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("wipe_records.id"), unique=True
    )
    wipe_record: Mapped["WipeRecord"] = relationship(back_populates="ledger_entry")

    report_hash: Mapped[str] = mapped_column(String(64))  # same as WipeRecord.report_hash
    previous_hash: Mapped[str] = mapped_column(String(64))  # chain link
    entry_hash: Mapped[str] = mapped_column(String(64), unique=True)  # sha256(previous_hash + report_hash)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
