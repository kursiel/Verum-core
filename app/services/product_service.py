from sqlalchemy.orm import Session
from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductCreate
from app.models.product import Product

class ProductService:
    def __init__(self, db: Session):
        self.repo = ProductRepository(db)
        self.db = db

    def list_products(self, tenant_id: str, limit: int, offset: int) -> list[Product]:
        return self.repo.list(tenant_id=tenant_id, limit=limit, offset=offset)

    def create_product(self, tenant_id: str, data: ProductCreate) -> Product:
        # Aquí irían validaciones: SKU único por tenant, etc.
        product = self.repo.create(tenant_id=tenant_id, **data.model_dump())
        self.db.commit()
        return product
