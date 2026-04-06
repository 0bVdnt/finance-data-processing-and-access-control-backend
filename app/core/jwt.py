from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import jwt

from app.config import get_settings


def create_access_token(user_id: UUID, role: str) -> str:
    """
    Create a JWT access token.

    The token contains:
        - sub: userID (subject)
        - role: user's role for quick access in middleware
        - exp: expiration timestamp
        - iat: issued at timestamp
    """

    settings = get_settings()
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Raises JWTError if the token is invalid or expired.
    Returns the payload dict with 'sub' and 'role'.
    """
    settings = get_settings()

    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
