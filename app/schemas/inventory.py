from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.entities import MovementType
from app.schemas.common import ORMModel


class MovementCreate(BaseModel):
    type: MovementType
    product_id: UUID
    qty: float = Field(gt=0)
    from_warehouse_id: UUID | None = None
    to_warehouse_id: UUID | None = None
    reference: str | None = None
    idempotency_key: str | None = None
    adjust_to_quantity: float | None = Field(default=None, ge=0)


class MovementOut(ORMModel):
    id: UUID
    type: MovementType
    qty: float
    product_id: UUID
    from_warehouse_id: UUID | None
    to_warehouse_id: UUID | None
    reference: str | None
    created_at: datetime


class BalanceOut(ORMModel):
    product_id: UUID
    warehouse_id: UUID
    qty: float
