"""
Safe demo detector: treats a regular file (or loopback image) as the
"device" being wiped. This is what you should use for live hackathon
demos and all local testing — it never touches real hardware.

For a real deployment, see linux_block_device.py, which detects an actual
block device (e.g. /dev/sda) and reads its real model/serial via lsblk.
"""
import hashlib
import os
import uuid

from src.detectors.base import DeviceDetector, DeviceInfo


class FileTargetDetector(DeviceDetector):
    def detect(self, target: str) -> DeviceInfo:
        if not os.path.isfile(target):
            raise FileNotFoundError(
                f"Target file not found: {target}. For safety, this agent "
                f"only wipes regular files or explicit block devices you "
                f"pass with --target."
            )

        size_bytes = os.path.getsize(target)

        # Derive a stable, fake-but-consistent "serial" from the file's
        # absolute path so repeated runs against the same test file
        # produce the same device identity (useful for demo repeatability).
        path_hash = hashlib.sha256(os.path.abspath(target).encode()).hexdigest()[:12]
        serial = f"TESTFILE-{path_hash.upper()}"

        return DeviceInfo(
            serial=serial,
            model=f"Simulated test volume ({os.path.basename(target)})",
            device_type="TEST_FILE",
            size_bytes=size_bytes,
            supports_encryption=False,
        )
