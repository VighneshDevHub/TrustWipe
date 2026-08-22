"""
Real hardware detector for Linux block devices (e.g. /dev/sda, /dev/nvme0n1).

Uses `lsblk` (pre-installed on virtually every Linux distro) to read the
device's actual model, serial, size, and rotational flag — which tells us
HDD vs SSD. NVMe devices are identified by the `nvme` prefix in the device
name, since `lsblk` doesn't have a dedicated NVMe flag.

WARNING: only wire this detector to devices you intend to genuinely wipe.
Never point it at a system's boot disk without triple-checking the path.
"""
import json
import subprocess

from src.detectors.base import DeviceDetector, DeviceInfo


class LinuxBlockDeviceDetector(DeviceDetector):
    def detect(self, target: str) -> DeviceInfo:
        result = subprocess.run(
            [
                "lsblk", "-b", "-J", "-o",
                "NAME,MODEL,SERIAL,SIZE,ROTA,TYPE",
                target,
            ],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        device = data["blockdevices"][0]

        is_rotational = device.get("rota", True)
        is_nvme = "nvme" in target.lower()

        if is_nvme:
            device_type = "NVMe"
        elif not is_rotational:
            device_type = "SSD"
        else:
            device_type = "HDD"

        return DeviceInfo(
            serial=device.get("serial") or "UNKNOWN",
            model=device.get("model") or "UNKNOWN",
            device_type=device_type,
            size_bytes=int(device.get("size", 0)),
            # A real implementation would check for TCG Opal / ATA security
            # feature sets via `hdparm -I` or `nvme id-ctrl`; left as a
            # documented extension point for Phase 2 hardening.
            supports_encryption=(device_type in ("SSD", "NVMe")),
        )
