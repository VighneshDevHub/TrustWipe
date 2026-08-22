"""
Builds the exact JSON shape the Phase 1 backend expects at
POST /api/v1/wipes (see backend/app/schemas/wipe.py::WipeReportIn).
Keeping this in one place means the agent and backend can't silently
drift out of sync on field names.
"""
from datetime import datetime, timezone

from src.detectors.base import DeviceInfo
from src.wipers.base import WipeResult


def build_report(
    device: DeviceInfo,
    wipe_result: WipeResult,
    started_at: datetime,
    completed_at: datetime,
    verification_passed: bool,
    operator: str,
) -> dict:
    return {
        "device_serial": device.serial,
        "device_model": device.model,
        "device_type": device.device_type,
        "wipe_method": wipe_result.method_name,
        "started_at": started_at.astimezone(timezone.utc).isoformat(),
        "completed_at": completed_at.astimezone(timezone.utc).isoformat(),
        "verification_passed": verification_passed,
        "operator": operator,
    }
