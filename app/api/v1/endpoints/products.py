from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import Principal, get_current_principal, get_tenant_db, require_roles
from app.models import RoleEnum
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductOut)
def create_product(
    payload: ProductCreate,
    principal: Principal = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.MANAGER, RoleEnum.CLERK)),
    db: Session = Depends(get_tenant_db),
):
    return ProductService(db, principal.tenant_id).create(payload)


@router.get("", response_model=list[ProductOut])
def list_products(limit: int = 20, offset: int = 0, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_tenant_db)):
    return ProductService(db, principal.tenant_id).list(limit, offset)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    principal: Principal = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.MANAGER)),
    db: Session = Depends(get_tenant_db),
):
    return ProductService(db, principal.tenant_id).update(product_id, payload)
