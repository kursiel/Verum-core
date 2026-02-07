from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import Principal, get_current_principal
from app.core.db import get_db
from app.models import User
from app.schemas.auth import LoginRequest, MeResponse, RefreshRequest, RegisterTenantRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, summary="Register tenant and admin")
def register(payload: RegisterTenantRequest, db: Session = Depends(get_db)):
    return AuthService(db).register_tenant(payload)


@router.post("/login", response_model=TokenResponse, summary="Login and get tokens")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return AuthService(db).login(payload)


@router.post("/refresh", response_model=TokenResponse, summary="Rotate refresh token")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return AuthService(db).refresh(payload.refresh_token)


@router.get("/me", response_model=MeResponse, summary="Current principal")
def me(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    user = db.get(User, principal.user_id)
    return MeResponse(user_id=principal.user_id, tenant_id=principal.tenant_id, role=principal.role, email=user.email)
