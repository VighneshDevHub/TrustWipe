from datetime import datetime, timezone

from src.detectors.base import DeviceInfo
from src.report_builder import build_report
from src.wipers.base import WipeResult


def test_build_report_shape_matches_backend_schema():
    device = DeviceInfo(
        serial="SN123", model="Test Model", device_type="SSD",
        size_bytes=1024, supports_encryption=True,
    )
    wipe_result = WipeResult(
        method_name="NIST 800-88 Purge - Crypto Erase", passes=1, bytes_processed=1024
    )
    started = datetime(2026, 8, 22, 10, 0, 0, tzinfo=timezone.utc)
    completed = datetime(2026, 8, 22, 10, 0, 5, tzinfo=timezone.utc)

    report = build_report(
        device=device,
        wipe_result=wipe_result,
        started_at=started,
        completed_at=completed,
        verification_passed=True,
        operator="test-operator",
    )

    # These keys must exactly match backend/app/schemas/wipe.py::WipeReportIn
    expected_keys = {
        "device_serial", "device_model", "device_type", "wipe_method",
        "started_at", "completed_at", "verification_passed", "operator",
    }
    assert set(report.keys()) == expected_keys
    assert report["device_serial"] == "SN123"
    assert report["verification_passed"] is True
