# Verum Inventory SaaS (MVP)

Backend multi-tenant para inventario con FastAPI + PostgreSQL + RLS.

## Decisiones de arquitectura
- **Multi-tenant shared schema** con `tenant_id` en tablas de negocio.
- **Aislamiento fuerte con RLS**: políticas por tabla usando `current_setting('app.tenant_id')`.
- **Tenant source of truth**: el `tenant_id` se deriva del JWT (nunca de headers arbitrarios).
- **Usuarios globales + memberships (`user_tenants`)** para soportar usuario en múltiples empresas.
- **RBAC simple** por rol en membership (`ADMIN`, `MANAGER`, `CLERK`, `READ_ONLY`).
- **Inventario** con tabla `inventory_balances` (materializada) + `stock_movements` (ledger).
- **Concurrencia**: `SELECT ... FOR UPDATE` en balances para evitar sobreventa.
- **Outbox scaffold** para futura integración con Hacienda/Celery/RQ.

## Requisitos
- Python 3.11+ (objetivo 3.12)
- Docker y Docker Compose

## Variables de entorno
Crear `.env` (ejemplo):

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/verum
JWT_SECRET=super-secret-change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["*"]
SUPERADMIN_BYPASS_RLS=false
```

## Levantar PostgreSQL
```bash
docker compose up -d postgres redis
```
Opcional: `pgadmin` también está en `docker-compose.yml`.

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Migraciones
```bash
alembic upgrade head
```

## Ejecutar API
```bash
uvicorn app.main:app --reload
```

## Ejecutar tests
```bash
pytest -q
```

## Endpoints base
Todo bajo `/api/v1`.

## Flujo curl (MVP)
### 1) Crear tenant + admin
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name":"Acme CR",
    "slug":"acme",
    "admin_email":"admin@acme.com",
    "admin_name":"Admin Acme",
    "password":"SuperSecret123"
  }'
```

### 2) Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@acme.com","password":"SuperSecret123","tenant_slug":"acme"}'
```

### 3) Crear producto
```bash
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"sku":"SKU-001","name":"Producto 1","unit":"UN","cost":1000,"price":1500}'
```

### 4) Crear bodega
```bash
curl -X POST http://localhost:8000/api/v1/warehouses \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Central","address":"San José"}'
```

### 5) Movimiento IN
```bash
curl -X POST http://localhost:8000/api/v1/inventory/movements \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"type":"IN","product_id":"<PRODUCT_ID>","qty":10,"to_warehouse_id":"<WAREHOUSE_ID>","reference":"OC-1"}'
```

### 6) Movimiento OUT
```bash
curl -X POST http://localhost:8000/api/v1/inventory/movements \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"type":"OUT","product_id":"<PRODUCT_ID>","qty":2,"from_warehouse_id":"<WAREHOUSE_ID>","reference":"VENTA-1"}'
```

### 7) Movimiento TRANSFER
```bash
curl -X POST http://localhost:8000/api/v1/inventory/movements \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"type":"TRANSFER","product_id":"<PRODUCT_ID>","qty":1,"from_warehouse_id":"<WH1>","to_warehouse_id":"<WH2>","reference":"TR-1"}'
```

### 8) Balances
```bash
curl "http://localhost:8000/api/v1/inventory/balances?limit=20&offset=0" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 9) Kardex
```bash
curl "http://localhost:8000/api/v1/inventory/kardex/<PRODUCT_ID>?limit=50&offset=0" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## RLS: cómo funciona
En cada request autenticado:
1. Se valida JWT.
2. Se obtiene `tenant_id` y `user_id` del token.
3. Se ejecuta `set_config('app.tenant_id', ...)` y `set_config('app.is_superadmin', ...)`.
4. PostgreSQL aplica policy por tabla:

```sql
tenant_id = current_setting('app.tenant_id', true)::uuid
```

Con bypass controlado:
```sql
current_setting('app.is_superadmin', true) = 'on'
```

## Futuro: Hacienda / Jobs
- Se deja `app/events/outbox.py` + tabla `outbox_events`.
- Futuro worker (Celery/RQ + Redis) publicará eventos pendientes.
- Estrategia esperada: retries exponenciales, idempotencia por `event_id`/`aggregate_id`.
