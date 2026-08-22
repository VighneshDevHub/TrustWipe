from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WipeResult:
    method_name: str  # human-readable, e.g. "NIST 800-88 Purge - Crypto Erase"
    passes: int
    bytes_processed: int


class Wiper(ABC):
    method_name: str

    @abstractmethod
    def wipe(self, target: str, size_bytes: int) -> WipeResult:
        """Perform the wipe on `target`. Must be idempotent-safe to call
        once per report (agent does not retry automatically)."""
        raise NotImplementedError
