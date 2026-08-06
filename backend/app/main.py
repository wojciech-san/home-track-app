from fastapi import FastAPI

from app.core.db import Base, engine
from app.routers import properties, usage, utility_types

app = FastAPI(title="Home Track API", version="0.1.0")

app.include_router(properties.router)
app.include_router(utility_types.router)
app.include_router(usage.router)


@app.on_event("startup")
def on_startup():
    # Creates tables that don't exist yet. Harmless against an existing DB.
    # Once the schema stabilizes, replace this with Alembic migrations.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}
