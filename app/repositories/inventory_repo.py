from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InventoryBalance, StockMovement


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_balance_for_update(self, tenant_id: UUID, product_id: UUID, warehouse_id: UUID) -> InventoryBalance | None:
        stmt = (
            select(InventoryBalance)
            .where(
                InventoryBalance.tenant_id == tenant_id,
                InventoryBalance.product_id == product_id,
                InventoryBalance.warehouse_id == warehouse_id,
            )
            .with_for_update()
        )
        return self.db.scalar(stmt)

    def create_balance(self, tenant_id: UUID, product_id: UUID, warehouse_id: UUID) -> InventoryBalance:
        b = InventoryBalance(tenant_id=tenant_id, product_id=product_id, warehouse_id=warehouse_id, qty=0)
        self.db.add(b)
        self.db.flush()
        return b

    def add_movement(self, movement: StockMovement) -> StockMovement:
        self.db.add(movement)
        self.db.flush()
        self.db.refresh(movement)
        return movement

    def get_idempotent(self, tenant_id: UUID, key: str) -> StockMovement | None:
        stmt = select(StockMovement).where(StockMovement.tenant_id == tenant_id, StockMovement.idempotency_key == key)
        return self.db.scalar(stmt)
