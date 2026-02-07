from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def set_tenant_context(db: Session, tenant_id: UUID, is_superadmin: bool = False) -> None:
    db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id": str(tenant_id)})
    db.execute(text("SELECT set_config('app.is_superadmin', :flag, true)"), {"flag": "on" if is_superadmin else "off"})
