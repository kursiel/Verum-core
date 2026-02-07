from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Product
from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = ProductRepository(db)

    def create(self, payload: ProductCreate) -> Product:
        product = Product(tenant_id=self.tenant_id, **payload.model_dump())
        try:
            self.repo.create(product)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Duplicate sku or invalid relation")
        return product

    def list(self, limit: int, offset: int) -> list[Product]:
        return self.repo.list(limit, offset)

    def update(self, product_id: UUID, payload: ProductUpdate) -> Product:
        product = self.repo.get(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, key, value)
        self.db.commit()
        self.db.refresh(product)
        return product
