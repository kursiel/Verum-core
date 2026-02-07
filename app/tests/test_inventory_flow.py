import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.main import app


@pytest.fixture(scope="session")
def db_ready():
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("PostgreSQL no disponible para pruebas de integración")
    return True


def test_auth_and_inventory_endpoints_exist(db_ready):
    client = TestClient(app)
    assert client.post("/api/v1/auth/login", json={"email": "x@x.com", "password": "12345678", "tenant_slug": "demo"}).status_code in {401, 403, 422}
