from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address: str | None = None


class WarehouseUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    is_active: bool | None = None


class WarehouseOut(ORMModel):
    id: UUID
    name: str
    address: str | None
    is_active: bool
