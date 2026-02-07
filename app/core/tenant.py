from dataclasses import dataclass
from fastapi import Header, HTTPException

@dataclass(frozen=True)
class TenantContext:
    tenant_id: str

def get_tenant(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id")) -> TenantContext:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="Missing X-Tenant-Id")
    return TenantContext(tenant_id=x_tenant_id)
