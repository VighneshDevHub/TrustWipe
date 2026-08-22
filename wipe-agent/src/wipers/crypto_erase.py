"""
NIST 800-88 "Purge" via Crypto Erase — for self-encrypting drives (most
modern SSDs/NVMe), the fastest and safest option: instead of overwriting
every block, destroy the encryption key the drive uses internally. Every
block on the drive instantly becomes unrecoverable ciphertext with no key
to decrypt it — no wear added to the drive, and it completes in
milliseconds instead of minutes/hours.

On real hardware this is done via `hdparm --security-erase-enhanced` (for
ATA Security Feature Set SEDs) or vendor-specific TCG Opal tooling. There
is no meaningful software-only way to demonstrate real key destruction
against a file target, so this simulator generates a random key, discards
it, and — to make the demo honest rather than a no-op — also does one
fast randomized overwrite of the file so the "before/after" content
visibly differs, exactly mirroring what a real crypto-erase achieves
from an external observer's point of view (unreadable content, near
instant completion).
"""
import os
import secrets

from src.wipers.base import Wiper, WipeResult

CHUNK_SIZE = 4 * 1024 * 1024  # larger chunks — crypto-erase is fast


class CryptoEraseWiper(Wiper):
    method_name = "NIST 800-88 Purge - Crypto Erase"

    def wipe(self, target: str, size_bytes: int) -> WipeResult:
        # Simulate generating and then immediately discarding the device's
        # internal encryption key. In real SED hardware this key never
        # leaves the drive controller — we never persist it here either.
        _ephemeral_key = secrets.token_bytes(32)
        del _ephemeral_key

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
