"""
Device detection interface.

A real deployment detects actual physical drives (via `lsblk`/`hdparm` on
Linux, WMI on Windows) and reads their model/serial/type straight from
the hardware. For a hackathon MVP demo — where wiping a real production
disk live on stage would be reckless — we detect a *target file* instead
and treat it as a stand-in "device". The interface is identical either
way, so swapping in real hardware detection later doesn't touch any
other part of the agent.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class DeviceInfo:
    serial: str
    model: str
    device_type: str  # "HDD" | "SSD" | "NVMe" | "USB" | "TEST_FILE"
    size_bytes: int
    supports_encryption: bool = False  # relevant for crypto-erase eligibility


class DeviceDetector(ABC):
    @abstractmethod
    def detect(self, target: str) -> DeviceInfo:
        """Inspect `target` (a device path or file path) and return its
        DeviceInfo. Must never raise for a missing target — callers should
        check existence before calling detect()."""
        raise NotImplementedError
