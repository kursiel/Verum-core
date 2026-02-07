from fastapi import FastAPI
from app.api.v1.router import api_router

def create_app() -> FastAPI:
    app = FastAPI(title="Verum Inventory Control")
    app.include_router(api_router, prefix="/api/v1")


    # DEBUG: imprimir rutas registradas
    for r in app.routes:
        print(r.path, getattr(r, "methods", None))

    return app

app = create_app()