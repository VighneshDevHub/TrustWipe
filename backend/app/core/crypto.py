"""
Cryptographic signing service.

This is the trust root of the whole system: every certificate is signed
with an ECDSA (secp256r1 / P-256) private key held only by the backend.
Anyone can verify a signature using the corresponding public key without
ever needing to trust our database directly.

Design notes:
- We sign the SHA-256 hash of the *canonical* JSON representation of a
  wipe report (sorted keys, no whitespace) so that signature verification
  is 100% deterministic regardless of how the JSON was formatted upstream.
- In production, SIGNING_PRIVATE_KEY_PEM must be injected via a secrets
  manager and rotated periodically. Never log or return the private key.
"""
import hashlib
import json
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

from app.core.config import get_settings

settings = get_settings()


def generate_keypair() -> tuple[str, str]:
    """Generate a new ECDSA (P-256) keypair. Returns (private_pem, public_pem).

    Used once to provision a real deployment's signing key, or automatically
    at dev startup if no key is configured. The output private_pem should be
    stored in a secrets manager for production use.
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


def canonical_json(data: dict[str, Any]) -> bytes:
    """Deterministic JSON encoding: sorted keys, no extra whitespace.

    Any two callers with the same logical data always produce the exact
    same bytes here — this is what makes hash + signature checks reliable.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sign_payload(data: dict[str, Any], private_key_pem: str) -> tuple[str, str]:
    """Sign a dict payload. Returns (payload_hash_hex, signature_hex)."""
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(), password=None
    )
    payload_bytes = canonical_json(data)
    payload_hash_hex = sha256_hex(payload_bytes)

    signature = private_key.sign(payload_bytes, ec.ECDSA(hashes.SHA256()))
    return payload_hash_hex, signature.hex()


def verify_signature(
    data: dict[str, Any], signature_hex: str, public_key_pem: str
) -> bool:
    """Re-derive the canonical bytes from `data` and check the signature.

    Returns False (never raises) on any mismatch — invalid signature,
    tampered data, or malformed hex — so callers can treat this as a
    simple pass/fail trust check.
    """
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        payload_bytes = canonical_json(data)
        signature = bytes.fromhex(signature_hex)
        public_key.verify(signature, payload_bytes, ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def get_or_create_dev_keypair() -> tuple[str, str]:
    """Dev convenience: use configured keys, or generate + print a fresh pair.

    In production, ALWAYS set SIGNING_PRIVATE_KEY_PEM / SIGNING_PUBLIC_KEY_PEM
    via your secrets manager so the key is stable across restarts — a new
    key on every restart would invalidate every previously issued certificate.
    """
    if settings.SIGNING_PRIVATE_KEY_PEM and settings.SIGNING_PUBLIC_KEY_PEM:
        return settings.SIGNING_PRIVATE_KEY_PEM, settings.SIGNING_PUBLIC_KEY_PEM

    private_pem, public_pem = generate_keypair()
    print(
        "\n[trustwipe] WARNING: no signing key configured — generated an "
        "EPHEMERAL dev keypair. Certificates signed now will fail "
        "verification after a restart. Set SIGNING_PRIVATE_KEY_PEM and "
        "SIGNING_PUBLIC_KEY_PEM in your .env for persistent signing.\n"
    )
    return private_pem, public_pem
