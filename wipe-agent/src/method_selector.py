"""
Picks the appropriate wipe method for a detected device, following
NIST 800-88 guidance rather than applying one method to every device:

- Self-encrypting SSD/NVMe -> Crypto Erase (fast, no unnecessary wear)
- Spinning HDD             -> Purge (multi-pass / native secure erase)
- Safe demo file target    -> Clear (fast, sufficient for a non-real device)

This mapping is itself a talking point in a hackathon pitch: naive tools
apply the same slow multi-pass overwrite to every device, which is both
wrong (unnecessary SSD wear) and slow. Auto-selecting the method shows
real domain understanding of the standard.
"""
from src.wipers.base import Wiper
from src.wipers.clear import ClearWiper
from src.wipers.crypto_erase import CryptoEraseWiper
from src.wipers.purge import PurgeWiper


def select_wiper(device_type: str, supports_encryption: bool) -> Wiper:
    if device_type == "TEST_FILE":
        return ClearWiper()
    if supports_encryption and device_type in ("SSD", "NVMe"):
        return CryptoEraseWiper()
    if device_type == "HDD":
        return PurgeWiper()
    # Unknown or USB flash — default to Clear as a safe baseline
    return ClearWiper()
