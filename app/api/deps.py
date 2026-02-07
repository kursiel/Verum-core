from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.tenant import get_tenant, TenantContext

def db_dep() -> Session:
    return Depends(get_db)

def tenant_dep() -> TenantContext:
    return Depends(get_tenant)
