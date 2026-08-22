from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class WipeReportIn(BaseModel):
    """What the Wipe Agent sends after completing a wipe. This is the
    untrusted input — the backend re-derives the hash and signature,
    it never trusts a hash/signature if the agent tried to send one."""

    device_serial: str = Field(min_length=1, max_length=128)
    device_model: str = Field(min_length=1, max_length=128)
    device_type: str = Field(min_length=1, max_length=64)
    wipe_method: str = Field(min_length=1, max_length=128)
    started_at: datetime
    completed_at: datetime
    verification_passed: bool
    operator: str = Field(min_length=1, max_length=128)

    @field_validator("completed_at")
    @classmethod
    def completed_after_started(cls, v: datetime, info):
        started = info.data.get("started_at")
        if started and v < started:
            raise ValueError("completed_at cannot be before started_at")
        return v


class CertificateOut(BaseModel):
    certificate_id: str
    device_serial: str
    device_model: str
    device_type: str
    wipe_method: str
    started_at: datetime
    completed_at: datetime
    verification_passed: bool
    operator: str
    report_hash: str
    signature: str
    ledger_sequence_number: int
    created_at: datetime

    model_config = {"from_attributes": True}


class VerificationResult(BaseModel):
    certificate_id: str
    signature_valid: bool
    chain_intact: bool
    overall_verified: bool
    detail: str
