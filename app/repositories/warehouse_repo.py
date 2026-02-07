from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Warehouse


class WarehouseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, warehouse: Warehouse) -> Warehouse:
        self.db.add(warehouse)
        self.db.flush()
        self.db.refresh(warehouse)
        return warehouse

    def get(self, warehouse_id: UUID) -> Warehouse | None:
        return self.db.get(Warehouse, warehouse_id)

    def list(self, limit: int, offset: int) -> list[Warehouse]:
        return list(self.db.scalars(select(Warehouse).offset(offset).limit(limit).order_by(Warehouse.name)))
