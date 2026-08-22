from app.core.crypto import get_or_create_dev_keypair
from app.db.session import get_db  # re-exported for convenience

# Cache the dev keypair at process level so it's stable for the life of
# the running process (still ephemeral across restarts unless configured
# via env vars — see app/core/crypto.py docstring).
_cached_keys: tuple[str, str] | None = None


def get_signing_keys() -> tuple[str, str]:
    global _cached_keys
    if _cached_keys is None:
        _cached_keys = get_or_create_dev_keypair()
    return _cached_keys


__all__ = ["get_db", "get_signing_keys"]
