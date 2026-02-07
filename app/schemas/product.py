from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    unit: str = "UN"
    cost: float = 0
    price: float = 0
    category_id: UUID | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    unit: str | None = None
    cost: float | None = None
    price: float | None = None
    is_active: bool | None = None
    category_id: UUID | None = None


class ProductOut(ORMModel):
    id: UUID
    sku: str
    name: str
    description: str | None
    unit: str
    cost: float
    price: float
    is_active: bool
