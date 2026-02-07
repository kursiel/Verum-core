from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.entities import RoleEnum


class RegisterTenantRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=150)
    slug: str = Field(min_length=2, max_length=100)
    admin_email: EmailStr
    admin_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_slug: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenClaims(BaseModel):
    sub: UUID
    tenant_id: UUID
    role: RoleEnum | None = None
    type: str
    jti: str
    exp: datetime


class MeResponse(BaseModel):
    user_id: UUID
    tenant_id: UUID
    role: RoleEnum
    email: EmailStr
