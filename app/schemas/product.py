from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    cost: float = Field(ge=0)

class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    cost: float

    class Config:
        from_attributes = True
