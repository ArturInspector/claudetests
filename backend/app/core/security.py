from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.config import get_settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return an Argon2 hash of the given password."""
    return _hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored hash."""
    try:
        return _hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False
    except Exception:
        # Argon2 can raise on malformed hashes; treat as invalid.
        return False


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    """Generate a signed JWT access token."""
    settings = get_settings()
    expire_delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expire_delta
    to_encode = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])











