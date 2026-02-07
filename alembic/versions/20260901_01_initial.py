"""initial

Revision ID: 20260901_01
Revises:
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260901_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    role_enum = sa.Enum("ADMIN", "MANAGER", "CLERK", "READ_ONLY", name="role_enum")
    role_enum.create(op.get_bind(), checkfirst=True)
    movement_enum = sa.Enum("IN", "OUT", "TRANSFER", "ADJUST", name="movement_type")
    movement_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "user_tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_user_tenant"),
    )
    op.create_index("ix_user_tenants_tenant_user", "user_tenants", ["tenant_id", "user_id"])

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_category_tenant_name"),
    )
    op.create_index("ix_categories_tenant_name", "categories", ["tenant_id", "name"])

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL")),
        sa.Column("sku", sa.String(60), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("unit", sa.String(30), nullable=False),
        sa.Column("cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "sku", name="uq_product_tenant_sku"),
    )
    op.create_index("ix_products_tenant_sku", "products", ["tenant_id", "sku"])
    op.create_index("ix_products_tenant_name", "products", ["tenant_id", "name"])

    op.create_table(
        "warehouses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("address", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_warehouse_tenant_name"),
    )
    op.create_index("ix_warehouse_tenant_name", "warehouses", ["tenant_id", "name"])

    op.create_table(
        "inventory_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("qty", sa.Numeric(14, 3), nullable=False, server_default=sa.text("0")),
        sa.CheckConstraint("qty >= 0", name="ck_inventory_qty_nonnegative"),
        sa.UniqueConstraint("tenant_id", "product_id", "warehouse_id", name="uq_balance_tenant_prod_wh"),
    )
    op.create_index("ix_balance_tenant_prod_wh", "inventory_balances", ["tenant_id", "product_id", "warehouse_id"])

    op.create_table(
        "stock_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", movement_enum, nullable=False),
        sa.Column("qty", sa.Numeric(14, 3), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id", ondelete="SET NULL")),
        sa.Column("to_warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id", ondelete="SET NULL")),
        sa.Column("reference", sa.String(120)),
        sa.Column("idempotency_key", sa.String(120)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_movement_tenant_idempotency"),
    )
    op.create_index("ix_movements_tenant_product_date", "stock_movements", ["tenant_id", "product_id", "created_at"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("aggregate_type", sa.String(80), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_outbox_tenant_created", "outbox_events", ["tenant_id", "created_at"])

    rls_tables = ["user_tenants", "categories", "products", "warehouses", "inventory_balances", "stock_movements", "outbox_events"]
    for table in rls_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation_{table}
            ON {table}
            USING (
                current_setting('app.is_superadmin', true) = 'on'
                OR tenant_id = current_setting('app.tenant_id', true)::uuid
            )
            WITH CHECK (
                current_setting('app.is_superadmin', true) = 'on'
                OR tenant_id = current_setting('app.tenant_id', true)::uuid
            )
            """
        )


def downgrade() -> None:
    for table in ["outbox_events", "stock_movements", "inventory_balances", "warehouses", "products", "categories", "user_tenants"]:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
    op.drop_table("outbox_events")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_movements_tenant_product_date", table_name="stock_movements")
    op.drop_table("stock_movements")
    op.drop_index("ix_balance_tenant_prod_wh", table_name="inventory_balances")
    op.drop_table("inventory_balances")
    op.drop_index("ix_warehouse_tenant_name", table_name="warehouses")
    op.drop_table("warehouses")
    op.drop_index("ix_products_tenant_name", table_name="products")
    op.drop_index("ix_products_tenant_sku", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_categories_tenant_name", table_name="categories")
    op.drop_table("categories")
    op.drop_index("ix_user_tenants_tenant_user", table_name="user_tenants")
    op.drop_table("user_tenants")
    op.drop_table("users")
    op.drop_table("tenants")
    sa.Enum(name="movement_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="role_enum").drop(op.get_bind(), checkfirst=True)
