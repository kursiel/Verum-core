from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.flush()
        self.db.refresh(product)
        return product

    def list(self, limit: int, offset: int) -> list[Product]:
        stmt = select(Product).offset(offset).limit(limit).order_by(Product.created_at.desc())
        return list(self.db.scalars(stmt))

    def get(self, product_id: UUID) -> Product | None:
        return self.db.get(Product, product_id)
