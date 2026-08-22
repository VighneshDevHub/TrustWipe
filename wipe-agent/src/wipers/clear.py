"""
NIST 800-88 "Clear" — a single overwrite pass with random data. Suitable
for low-sensitivity data or as a fast baseline. This is the method the
agent defaults to for HDDs and for the safe file-target demo mode.
"""
import os

from src.wipers.base import Wiper, WipeResult

CHUNK_SIZE = 1024 * 1024  # 1 MB


class ClearWiper(Wiper):
    method_name = "NIST 800-88 Clear (single-pass overwrite)"

    def wipe(self, target: str, size_bytes: int) -> WipeResult:
        bytes_written = 0
        with open(target, "r+b") as f:
            f.seek(0)
            while bytes_written < size_bytes:
                chunk = min(CHUNK_SIZE, size_bytes - bytes_written)
                f.write(os.urandom(chunk))
                bytes_written += chunk
            f.flush()
            os.fsync(f.fileno())

        return WipeResult(
            method_name=self.method_name, passes=1, bytes_processed=bytes_written
        )
