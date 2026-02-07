from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.tenant import TenantContext, get_tenant
from app.schemas.product import ProductCreate, ProductOut
from app.services.product_service import ProductService

router = APIRouter()

@router.get("/", response_model=list[ProductOut])
def list_products(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db), tenant: TenantContext = Depends(get_tenant),):
    svc = ProductService(db)
    return svc.list_products(tenant_id=tenant.tenant_id, limit=limit, offset=offset)


@router.post("/", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), tenant: TenantContext = Depends(get_tenant),):
    svc = ProductService(db)
    return svc.create_product(tenant_id=tenant.tenant_id, data=payload)
