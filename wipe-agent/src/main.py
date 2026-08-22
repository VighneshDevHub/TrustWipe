"""
Wipe Agent CLI.

Usage (safe demo mode — wipes a regular file, never real hardware):
    python -m src.main --target /path/to/test_volume.img --operator "demo-operator"

Usage (real Linux block device — DANGEROUS, double-check the path):
    python -m src.main --target /dev/sdb --operator "tech-01" --real-device
"""
import argparse
import sys
from datetime import datetime, timezone

from src.api_client import ApiClient
from src.detectors.file_target import FileTargetDetector
from src.method_selector import select_wiper
from src.report_builder import build_report
from src.verifier import capture_pre_wipe_samples, verify_wipe


def run(target: str, operator: str, api_url: str, real_device: bool) -> dict:
    if real_device:
        # Import here, not at module load, so the file-target demo path
        # never requires lsblk / a Linux environment to run.
        from src.detectors.linux_block_device import LinuxBlockDeviceDetector

        detector = LinuxBlockDeviceDetector()
        print(
            f"[WARNING] --real-device set. About to detect and wipe {target}. "
            f"This is IRREVERSIBLE. Press Ctrl+C now to abort.",
            file=sys.stderr,
        )
    else:
        detector = FileTargetDetector()

    device = detector.detect(target)
    print(f"[detect] {device.device_type} — {device.model} (serial: {device.serial})")

    wiper = select_wiper(device.device_type, device.supports_encryption)
    print(f"[select] Method: {wiper.method_name}")

    pre_wipe_samples = capture_pre_wipe_samples(target, device.size_bytes)

    started_at = datetime.now(timezone.utc)
    print("[wipe] Starting...")
    wipe_result = wiper.wipe(target, device.size_bytes)
    completed_at = datetime.now(timezone.utc)
    print(
        f"[wipe] Done — {wipe_result.passes} pass(es), "
        f"{wipe_result.bytes_processed} bytes processed."
    )

    print("[verify] Sampling random offsets for read-back verification...")
    verification = verify_wipe(target, pre_wipe_samples)
    print(
        f"[verify] {verification.samples_changed}/{verification.samples_checked} "
        f"sampled regions confirmed wiped."
    )

    report = build_report(
        device=device,
        wipe_result=wipe_result,
        started_at=started_at,
        completed_at=completed_at,
        verification_passed=verification.passed,
        operator=operator,
    )

    print(f"[report] Submitting to {api_url}...")
    client = ApiClient(base_url=api_url)
    certificate = client.submit_wipe_report(report)
    print(f"[report] Certificate issued: {certificate['certificate_id']}")

    return certificate


def main():
    parser = argparse.ArgumentParser(description="TrustWipe agent")
    parser.add_argument("--target", required=True, help="Path to file or device to wipe")
    parser.add_argument("--operator", required=True, help="Operator/station identifier")
    parser.add_argument(
        "--api-url", default="http://localhost:8000", help="Backend base URL"
    )
    parser.add_argument(
        "--real-device",
        action="store_true",
        help="DANGER: treat --target as a real Linux block device, not a test file",
    )
    args = parser.parse_args()

    run(
        target=args.target,
        operator=args.operator,
        api_url=args.api_url,
        real_device=args.real_device,
    )


if __name__ == "__main__":
    main()
