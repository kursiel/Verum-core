from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.security import decode_token
from app.core.tenant import set_tenant_context
from app.models import RoleEnum, User, UserTenant

bearer_scheme = HTTPBearer(auto_error=True)


@dataclass
class Principal:
    user_id: UUID
    tenant_id: UUID
    role: RoleEnum
    email: str


def get_current_principal(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)
) -> Principal:
    payload = decode_token(creds.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
    user_id = UUID(payload["sub"])
    tenant_id = UUID(payload["tenant_id"])
    membership = db.scalar(select(UserTenant).where(UserTenant.user_id == user_id, UserTenant.tenant_id == tenant_id))
    if not membership:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Membership not found")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    return Principal(user_id=user_id, tenant_id=tenant_id, role=membership.role, email=user.email)


def get_tenant_db(
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)
):
    is_superadmin = settings.superadmin_bypass_rls and principal.role == RoleEnum.ADMIN
    set_tenant_context(db, principal.tenant_id, is_superadmin=is_superadmin)
    return db


def require_roles(*allowed: RoleEnum):
    def checker(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return principal

    return checker
