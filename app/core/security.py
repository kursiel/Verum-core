from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_token(payload: dict, expires_delta: timedelta) -> str:
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "jti": str(uuid4())})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID, tenant_id: UUID, role: str) -> str:
    return create_token(
        {"sub": str(user_id), "tenant_id": str(tenant_id), "role": role, "type": "access"},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: UUID, tenant_id: UUID) -> str:
    return create_token(
        {"sub": str(user_id), "tenant_id": str(tenant_id), "type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
