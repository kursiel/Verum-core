from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import Principal, get_current_principal, get_tenant_db, require_roles
from app.models import RoleEnum
from app.schemas.inventory import BalanceOut, MovementCreate, MovementOut
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/movements", response_model=MovementOut, summary="Create stock movement")
def create_movement(
    payload: MovementCreate,
    principal: Principal = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.MANAGER, RoleEnum.CLERK)),
    db: Session = Depends(get_tenant_db),
):
    return InventoryService(db, principal.tenant_id, principal.user_id).move(payload)


@router.get("/balances", response_model=list[BalanceOut], summary="List balances by warehouse")
def balances(limit: int = 20, offset: int = 0, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_tenant_db)):
    return InventoryService(db, principal.tenant_id, principal.user_id).balances(limit, offset)


@router.get("/kardex/{product_id}", response_model=list[MovementOut], summary="Kardex by product")
def kardex(product_id: UUID, limit: int = 50, offset: int = 0, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_tenant_db)):
    return InventoryService(db, principal.tenant_id, principal.user_id).kardex(product_id, limit, offset)
