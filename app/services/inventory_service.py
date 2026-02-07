from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InventoryBalance, MovementType, Product, StockMovement, Warehouse
from app.repositories.inventory_repo import InventoryRepository
from app.schemas.inventory import MovementCreate


class InventoryService:
    def __init__(self, db: Session, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.repo = InventoryRepository(db)

    def move(self, payload: MovementCreate) -> StockMovement:
        if payload.idempotency_key:
            found = self.repo.get_idempotent(self.tenant_id, payload.idempotency_key)
            if found:
                return found

        product = self.db.get(Product, payload.product_id)
        if not product:
            raise HTTPException(404, "Product not found")
        if payload.from_warehouse_id and not self.db.get(Warehouse, payload.from_warehouse_id):
            raise HTTPException(404, "from_warehouse not found")
        if payload.to_warehouse_id and not self.db.get(Warehouse, payload.to_warehouse_id):
            raise HTTPException(404, "to_warehouse not found")

        qty = Decimal(str(payload.qty))
        with self.db.begin_nested():
            if payload.type == MovementType.IN:
                self._add(payload.product_id, payload.to_warehouse_id, qty)
            elif payload.type == MovementType.OUT:
                self._remove(payload.product_id, payload.from_warehouse_id, qty)
            elif payload.type == MovementType.TRANSFER:
                if payload.from_warehouse_id == payload.to_warehouse_id:
                    raise HTTPException(400, "Warehouses must be different")
                self._remove(payload.product_id, payload.from_warehouse_id, qty)
                self._add(payload.product_id, payload.to_warehouse_id, qty)
            elif payload.type == MovementType.ADJUST:
                if payload.adjust_to_quantity is None:
                    raise HTTPException(400, "adjust_to_quantity is required for ADJUST")
                self._set_qty(payload.product_id, payload.to_warehouse_id or payload.from_warehouse_id, Decimal(str(payload.adjust_to_quantity)))

            movement = StockMovement(
                tenant_id=self.tenant_id,
                type=payload.type,
                qty=qty,
                product_id=payload.product_id,
                from_warehouse_id=payload.from_warehouse_id,
                to_warehouse_id=payload.to_warehouse_id,
                reference=payload.reference,
                idempotency_key=payload.idempotency_key,
                created_by=self.user_id,
            )
            self.repo.add_movement(movement)
        self.db.commit()
        return movement

    def _get_or_create_locked_balance(self, product_id: UUID, warehouse_id: UUID) -> InventoryBalance:
        if warehouse_id is None:
            raise HTTPException(400, "Warehouse required")
        balance = self.repo.get_balance_for_update(self.tenant_id, product_id, warehouse_id)
        if not balance:
            balance = self.repo.create_balance(self.tenant_id, product_id, warehouse_id)
            self.db.flush()
            balance = self.repo.get_balance_for_update(self.tenant_id, product_id, warehouse_id)
        return balance

    def _add(self, product_id: UUID, warehouse_id: UUID | None, qty: Decimal) -> None:
        balance = self._get_or_create_locked_balance(product_id, warehouse_id)
        balance.qty = Decimal(str(balance.qty)) + qty

    def _remove(self, product_id: UUID, warehouse_id: UUID | None, qty: Decimal) -> None:
        balance = self._get_or_create_locked_balance(product_id, warehouse_id)
        current = Decimal(str(balance.qty))
        if current - qty < 0:
            raise HTTPException(409, "Insufficient stock")
        balance.qty = current - qty

    def _set_qty(self, product_id: UUID, warehouse_id: UUID | None, qty: Decimal) -> None:
        balance = self._get_or_create_locked_balance(product_id, warehouse_id)
        balance.qty = qty

    def balances(self, limit: int, offset: int):
        stmt = select(InventoryBalance).offset(offset).limit(limit).order_by(InventoryBalance.product_id)
        return list(self.db.scalars(stmt))

    def kardex(self, product_id: UUID, limit: int, offset: int):
        stmt = (
            select(StockMovement)
            .where(StockMovement.product_id == product_id)
            .order_by(StockMovement.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt))
