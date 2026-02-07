import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    CLERK = "CLERK"
    READ_ONLY = "READ_ONLY"


class MovementType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    TRANSFER = "TRANSFER"
    ADJUST = "ADJUST"


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class UserTenant(Base):
    __tablename__ = "user_tenants"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum, name="role_enum"), nullable=False, default=RoleEnum.CLERK)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_user_tenant"), Index("ix_user_tenants_tenant_user", "tenant_id", "user_id"))


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_category_tenant_name"), Index("ix_categories_tenant_name", "tenant_id", "name"))


class Product(Base):
    __tablename__ = "products"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    sku: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(30), default="UN", nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "sku", name="uq_product_tenant_sku"),
        Index("ix_products_tenant_sku", "tenant_id", "sku"),
        Index("ix_products_tenant_name", "tenant_id", "name"),
    )


class Warehouse(Base):
    __tablename__ = "warehouses"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_warehouse_tenant_name"), Index("ix_warehouse_tenant_name", "tenant_id", "name"))


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    warehouse_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    qty: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_id", "warehouse_id", name="uq_balance_tenant_prod_wh"),
        Index("ix_balance_tenant_prod_wh", "tenant_id", "product_id", "warehouse_id"),
        CheckConstraint("qty >= 0", name="ck_inventory_qty_nonnegative"),
    )


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[MovementType] = mapped_column(Enum(MovementType, name="movement_type"), nullable=False)
    qty: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    from_warehouse_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="SET NULL"))
    to_warehouse_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="SET NULL"))
    reference: Mapped[str | None] = mapped_column(String(120))
    idempotency_key: Mapped[str | None] = mapped_column(String(120))
    created_by: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    __table_args__ = (
        Index("ix_movements_tenant_product_date", "tenant_id", "product_id", "created_at"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_movement_tenant_idempotency"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    __table_args__ = (Index("ix_outbox_tenant_created", "tenant_id", "created_at"),)
