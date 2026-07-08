from fastapi import FastAPI

from .routers import demands, health, ingest, whatsapp, works

app = FastAPI(title="sunwai api", docs_url="/api/docs", openapi_url="/api/openapi.json")

app.include_router(health.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(demands.router, prefix="/api")
app.include_router(works.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")
