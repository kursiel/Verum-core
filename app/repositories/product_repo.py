from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.product import Product

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, tenant_id: str, limit: int = 50, offset: int = 0) -> list[Product]:
        stmt = (
            select(Product)
            .where(Product.tenant_id == tenant_id)
            .order_by(Product.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(self, tenant_id: str, sku: str, name: str, cost: float) -> Product:
        obj = Product(tenant_id=tenant_id, sku=sku, name=name, cost=cost)
        self.db.add(obj)
        self.db.flush()  # para obtener id sin commit todavía
        return obj
