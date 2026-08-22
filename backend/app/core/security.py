"""
Password hashing (bcrypt) and JWT issuance/verification for the
recycler dashboard login. This is a SEPARATE trust mechanism from the
ECDSA certificate signing in app/core/crypto.py — auth answers "is this
person allowed to view the dashboard", while crypto.py answers "is this
certificate authentic". Don't conflate the two keys.
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    """`subject` is typically the user's id or email — embedded as the
    JWT's `sub` claim."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Returns the subject (user identifier) if the token is valid and
    unexpired, otherwise None. Never raises — callers treat None as
    'unauthenticated'."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None
