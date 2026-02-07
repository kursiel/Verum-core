from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import Principal, get_current_principal, get_tenant_db, require_roles
from app.models import RoleEnum
from app.schemas.warehouse import WarehouseCreate, WarehouseOut, WarehouseUpdate
from app.services.warehouse_service import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.post("", response_model=WarehouseOut)
def create_warehouse(
    payload: WarehouseCreate,
    principal: Principal = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.MANAGER)),
    db: Session = Depends(get_tenant_db),
):
    return WarehouseService(db, principal.tenant_id).create(payload)


@router.get("", response_model=list[WarehouseOut])
def list_warehouses(limit: int = 20, offset: int = 0, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_tenant_db)):
    return WarehouseService(db, principal.tenant_id).list(limit, offset)


@router.patch("/{warehouse_id}", response_model=WarehouseOut)
def update_warehouse(
    warehouse_id: UUID,
    payload: WarehouseUpdate,
    principal: Principal = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.MANAGER)),
    db: Session = Depends(get_tenant_db),
):
    return WarehouseService(db, principal.tenant_id).update(warehouse_id, payload)
