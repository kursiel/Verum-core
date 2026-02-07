from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Warehouse
from app.repositories.warehouse_repo import WarehouseRepository
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate


class WarehouseService:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = WarehouseRepository(db)

    def create(self, payload: WarehouseCreate) -> Warehouse:
        warehouse = Warehouse(tenant_id=self.tenant_id, **payload.model_dump())
        try:
            self.repo.create(warehouse)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Warehouse already exists")
        return warehouse

    def list(self, limit: int, offset: int) -> list[Warehouse]:
        return self.repo.list(limit, offset)

    def update(self, warehouse_id: UUID, payload: WarehouseUpdate) -> Warehouse:
        warehouse = self.repo.get(warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(warehouse, key, value)
        self.db.commit()
        self.db.refresh(warehouse)
        return warehouse
