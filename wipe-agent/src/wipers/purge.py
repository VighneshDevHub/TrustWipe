"""
NIST 800-88 "Purge" — stronger erasure for higher-sensitivity data.

On real HDD hardware, Purge is properly implemented by invoking the
drive's own ATA Secure Erase command (via `hdparm --security-erase`) or
NVMe Sanitize (`nvme-cli sanitize`), which the drive firmware executes
internally — this is both more thorough and much faster than a
software-level overwrite, because it operates below the filesystem.

For the file-target demo (and as a software fallback for hardware that
doesn't support a native secure-erase command), we approximate Purge with
a 3-pass overwrite: two random passes plus a final zero pass, which
mirrors the classic DoD 5220.22-M pattern.

See `docs/phase2.md` for exactly which shell commands to swap in for
real ATA/NVMe secure erase in a production deployment.
"""
import os

from src.wipers.base import Wiper, WipeResult

CHUNK_SIZE = 1024 * 1024


class PurgeWiper(Wiper):
    method_name = "NIST 800-88 Purge (3-pass overwrite, software fallback)"

    def wipe(self, target: str, size_bytes: int) -> WipeResult:
        passes = 0
        with open(target, "r+b") as f:
            for pass_num in range(3):
                f.seek(0)
                bytes_written = 0
                while bytes_written < size_bytes:
                    chunk = min(CHUNK_SIZE, size_bytes - bytes_written)
                    if pass_num < 2:
                        f.write(os.urandom(chunk))
                    else:
                        f.write(b"\x00" * chunk)
                    bytes_written += chunk
                f.flush()
                os.fsync(f.fileno())
                passes += 1

        return WipeResult(
            method_name=self.method_name, passes=passes, bytes_processed=size_bytes
        )
