from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import RefreshToken, RoleEnum, Tenant, User, UserTenant
from app.schemas.auth import LoginRequest, RegisterTenantRequest, TokenResponse


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_tenant(self, payload: RegisterTenantRequest) -> TokenResponse:
        if self.db.scalar(select(Tenant).where(Tenant.slug == payload.slug)):
            raise HTTPException(status_code=400, detail="Tenant slug already exists")
        if self.db.scalar(select(User).where(User.email == payload.admin_email)):
            raise HTTPException(status_code=400, detail="Email already exists")

        tenant = Tenant(name=payload.company_name, slug=payload.slug)
        user = User(email=payload.admin_email, full_name=payload.admin_name, password_hash=hash_password(payload.password))
        self.db.add_all([tenant, user])
        self.db.flush()
        membership = UserTenant(tenant_id=tenant.id, user_id=user.id, role=RoleEnum.ADMIN, is_default=True)
        self.db.add(membership)

        tokens = self._issue_tokens(user.id, tenant.id, membership.role)
        self.db.commit()
        return tokens

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.db.scalar(select(User).where(User.email == payload.email))
        tenant = self.db.scalar(select(Tenant).where(Tenant.slug == payload.tenant_slug, Tenant.is_active.is_(True)))
        if not user or not tenant or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        membership = self.db.scalar(select(UserTenant).where(UserTenant.user_id == user.id, UserTenant.tenant_id == tenant.id))
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no access to tenant")
        tokens = self._issue_tokens(user.id, tenant.id, membership.role)
        self.db.commit()
        return tokens

    def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])

        token_db = self.db.scalar(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.tenant_id == tenant_id,
                RefreshToken.revoked.is_(False),
            )
        )
        if not token_db or not verify_password(refresh_token, token_db.token_hash) or token_db.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Refresh token revoked or expired")
        token_db.revoked = True

        membership = self.db.scalar(select(UserTenant).where(UserTenant.user_id == user_id, UserTenant.tenant_id == tenant_id))
        if not membership:
            raise HTTPException(status_code=403, detail="Membership not found")
        tokens = self._issue_tokens(user_id, tenant_id, membership.role)
        self.db.commit()
        return tokens

    def _issue_tokens(self, user_id: UUID, tenant_id: UUID, role: RoleEnum) -> TokenResponse:
        access = create_access_token(user_id, tenant_id, role.value)
        refresh = create_refresh_token(user_id, tenant_id)
        rt = RefreshToken(
            user_id=user_id,
            tenant_id=tenant_id,
            token_hash=hash_password(refresh),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        )
        self.db.add(rt)
        return TokenResponse(access_token=access, refresh_token=refresh)
