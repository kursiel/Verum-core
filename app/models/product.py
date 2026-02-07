from sqlalchemy import String, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)  # UUID string por simplicidad
    sku: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
