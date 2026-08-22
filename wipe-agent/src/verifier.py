"""
Read-back verification: after a wipe, sample random offsets across the
target and confirm the content no longer matches the pre-wipe baseline.

This is the step naive wipers skip — a tool that claims "wiped" without
ever reading back and checking is just trusting itself. Real production
verification also checks that no filesystem metadata (partition tables,
file allocation tables) remains readable; this MVP checks raw byte
content, which is sufficient to prove the point for the demo.
"""
import os
import random
from dataclasses import dataclass

SAMPLE_COUNT = 20
SAMPLE_SIZE = 512


@dataclass
class VerificationResult:
    passed: bool
    samples_checked: int
    samples_changed: int


def verify_wipe(target: str, pre_wipe_samples: list[tuple[int, bytes]]) -> VerificationResult:
    """Compare post-wipe content at the same offsets against pre-wipe
    samples captured by `capture_pre_wipe_samples`. If none of the sampled
    regions match their original content, verification passes."""
    changed = 0
    with open(target, "rb") as f:
        for offset, original_bytes in pre_wipe_samples:
            f.seek(offset)
            current_bytes = f.read(len(original_bytes))
            if current_bytes != original_bytes:
                changed += 1

    total = len(pre_wipe_samples)
    return VerificationResult(
        passed=(changed == total and total > 0),
        samples_checked=total,
        samples_changed=changed,
    )


def capture_pre_wipe_samples(target: str, size_bytes: int) -> list[tuple[int, bytes]]:
    """Grab SAMPLE_COUNT random (offset, original_bytes) pairs BEFORE
    wiping, so verify_wipe has something to compare against afterward."""
    if size_bytes <= SAMPLE_SIZE:
        offsets = [0]
    else:
        offsets = [
            random.randint(0, size_bytes - SAMPLE_SIZE) for _ in range(SAMPLE_COUNT)
        ]

    samples = []
    with open(target, "rb") as f:
        for offset in offsets:
            f.seek(offset)
            samples.append((offset, f.read(SAMPLE_SIZE)))
    return samples
