# Building the Home Track Backend From Scratch

A step-by-step walkthrough of how `backend/` is put together, in the order you'd build it yourself.
The goal: a FastAPI service backed by Postgres that tracks utility usage, cost, and tenant leases
across multiple properties.

## What you're building

Three ideas, three tables:

- **Property** — one of your rental units (name, address).
- **UtilityType** — a category of thing you pay for (water, energy, gas, rent), each with a unit
  (m3, kWh, PLN) and a `current_rate` (price per unit) so cost can be calculated automatically.
- **UsageRecord** — one reading for one property, one utility type, one month (e.g. "12.5 m3 of
  water at Downtown Apartment in August 2026").
- **Lease** — a tenant's rental agreement for a property (who's renting, monthly rent, start/end date).

Everything else — Pydantic schemas, routers, config — exists to safely get data in and out of those
tables over HTTP.

## Prerequisites

- Python 3.11+
- A Postgres database you can connect to (local, Docker, or managed — Supabase/Neon/RDS all work)
- `uv` (recommended) or plain `venv` + `pip`

## Step 1 — Project skeleton

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── db.py
│   └── routers/
│       ├── __init__.py
│       ├── properties.py
│       ├── utility_types.py
│       ├── usage.py
│       └── leases.py
├── scripts/
│   ├── __init__.py
│   └── seed_utility_types.py
├── requirements.txt
├── .env.example
└── README.md
```

Why this shape: `app/core/` holds infrastructure every router depends on (config, DB session) —
keeping it separate avoids circular imports. `app/routers/` has one file per resource so each stays
small. `models.py` (DB tables) and `schemas.py` (API request/response shapes) are deliberately
separate files, so the database structure doesn't have to match the JSON shape one-to-one.

Create the venv and install dependencies:

```bash
cd backend
uv venv
uv pip install -r requirements.txt   # see Step 2 for what's in this file
```

## Step 2 — `requirements.txt`

```
fastapi>=0.110
uvicorn[standard]>=0.29
sqlalchemy>=2.0
pydantic>=2.6
pydantic-settings>=2.2
psycopg2-binary>=2.9
python-dotenv>=1.0
```

`fastapi` + `uvicorn` are the web framework and dev server. `sqlalchemy` is the ORM. `pydantic` +
`pydantic-settings` handle request/response validation and reading config from environment
variables. `psycopg2-binary` is the Postgres driver SQLAlchemy needs. `python-dotenv` lets
`pydantic-settings` load a `.env` file.

## Step 3 — Configuration (`app/core/config.py`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, read from environment variables or a .env file."""

    database_url: str = "sqlite:///./home_track.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
```

One setting: `database_url`, defaulting to a local SQLite file so the app runs out of the box before
you've set up Postgres. `pydantic-settings` reads `.env` **relative to the current working
directory** — this matters later: `.env` has to exist (not just `.env.example`), and uvicorn has to
be started from inside `backend/`.

## Step 4 — Database engine and session (`app/core/db.py`)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: opens a session per request, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

`engine` is the connection pool to the database. `Base` is what every model class inherits from —
`Base.metadata` is how SQLAlchemy knows what tables to create. `get_db()` is a generator used as a
FastAPI dependency (`Depends(get_db)`): FastAPI calls it before your route runs, hands your route the
`db` session, then runs the `finally` block to close it after — one session per request, always
cleaned up.

## Step 5 — Models (`app/models.py`)

Define one class per table, inheriting from `Base`. Build them up one at a time:

**Property** — the root entity everything else hangs off:

```python
class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usage_records: Mapped[list["UsageRecord"]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )
    leases: Mapped[list["Lease"]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )
```

**UtilityType** — a category with a price per unit:

```python
class UtilityType(Base):
    __tablename__ = "utility_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # water, energy, gas, rent
    unit: Mapped[str | None] = mapped_column(String, nullable=True)  # m3, kWh, PLN, etc.
    current_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # price per unit

    usage_records: Mapped[list["UsageRecord"]] = relationship(
        back_populates="utility_type", cascade="all, delete-orphan"
    )
```

`current_rate` only affects *future* cost calculations (see Step 8) — past `usage_records.cost`
values are never recalculated retroactively.

**UsageRecord** — the actual monthly reading, one per property + utility type + month:

```python
class UsageRecord(Base):
    __tablename__ = "usage_records"
    __table_args__ = (
        UniqueConstraint("property_id", "utility_type_id", "month", name="uq_usage_property_utility_month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    utility_type_id: Mapped[int] = mapped_column(ForeignKey("utility_types.id"), nullable=False)
    month: Mapped[date] = mapped_column(Date, nullable=False)  # first day of the month
    value: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    property: Mapped["Property"] = relationship(back_populates="usage_records")
    utility_type: Mapped["UtilityType"] = relationship(back_populates="usage_records")
```

The `UniqueConstraint` is what makes "upsert by property + utility + month" possible later — the
database itself won't allow two rows for the same combination.

**Lease** — a tenant's rental agreement:

```python
class Lease(Base):
    __tablename__ = "leases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    tenant_name: Mapped[str] = mapped_column(String, nullable=False)
    tenant_email: Mapped[str | None] = mapped_column(String, nullable=True)
    tenant_phone: Mapped[str | None] = mapped_column(String, nullable=True)
    monthly_rent: Mapped[float] = mapped_column(Float, nullable=False)
    deposit: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # null = ongoing
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    property: Mapped["Property"] = relationship(back_populates="leases")
```

`end_date` nullable models "still renting" without needing a separate status flag.

## Step 6 — Schemas (`app/schemas.py`)

For each model, define the shapes the API accepts and returns. The pattern per resource:

- `*Base` — shared fields
- `*Create` — what a `POST` body looks like (usually just `Base`)
- `*Update` — what a `PATCH` body looks like (all fields optional, so partial updates work)
- `*Out` — what a response looks like (`Base` + `id` + timestamps), with
  `model_config = ConfigDict(from_attributes=True)` so it can be built directly from a SQLAlchemy
  object

Example for `UtilityType`:

```python
class UtilityTypeBase(BaseModel):
    name: str
    unit: str | None = None
    current_rate: float | None = None

class UtilityTypeCreate(UtilityTypeBase):
    pass

class UtilityTypeUpdate(BaseModel):
    unit: str | None = None
    current_rate: float | None = None

class UtilityTypeOut(UtilityTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
```

Repeat this shape for `Property`, `UsageRecord` (as `UsageRecordUpsert`/`UsageRecordOut` — there's no
separate update schema since `POST /usage` handles both create and update), and `Lease`. Also define
two response-only schemas that don't map to a table — `UtilitySummary` and `PropertySummary` — used
by the dashboard summary endpoint in Step 7.

## Step 7 — Routers (`app/routers/*.py`)

One file per resource, each holding an `APIRouter`. The pattern for a simple resource
(`properties.py`):

```python
router = APIRouter(prefix="/properties", tags=["properties"])

@router.get("", response_model=list[PropertyOut])
def list_properties(db: Session = Depends(get_db)):
    return db.scalars(select(Property).order_by(Property.name)).all()

@router.post("", response_model=PropertyOut, status_code=201)
def create_property(payload: PropertyCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Property).where(Property.name == payload.name))
    if existing:
        raise HTTPException(status_code=409, detail="Property with this name already exists")
    prop = Property(**payload.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop

@router.get("/{property_id}", response_model=PropertyOut)
def get_property(property_id: int, db: Session = Depends(get_db)):
    prop = db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop
```

`utility_types.py` follows the same list/create pattern, plus a `PATCH /{id}` for updating
`current_rate` without touching `name`.

`usage.py` is the most involved:

- `POST /usage` **upserts**: it looks for an existing row matching
  `property_id + utility_type_id + month` (the unique constraint from Step 5) and updates it if
  found, otherwise inserts. If the request body doesn't include `cost`, it's calculated as
  `value * utility_type.current_rate` — pass `cost` explicitly to override (e.g. a flat bill that
  doesn't follow the metered rate).
- `GET /usage/summary` groups records by property + month and returns per-utility totals — this is
  what a dashboard charts against, so it does the aggregation server-side instead of making the
  frontend do it.
- Route ordering matters: `/usage/summary` is defined **before** `/usage/{usage_id}`, otherwise
  FastAPI would try to parse `"summary"` as an integer path parameter and 422 the request.

`leases.py` adds a `PATCH` and `DELETE`, plus a `GET /leases?active_on=<date>` filter that finds the
lease covering a given date (`start_date <= date AND (end_date IS NULL OR end_date >= date)`).

## Step 8 — Wiring it together (`app/main.py`)

```python
from fastapi import FastAPI
from app.core.db import Base, engine
from app.routers import leases, properties, usage, utility_types

app = FastAPI(title="Home Track API", version="0.1.0")

app.include_router(properties.router)
app.include_router(utility_types.router)
app.include_router(usage.router)
app.include_router(leases.router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}
```

`create_all()` creates tables that don't exist yet — it's convenient for getting started but it
**never alters an existing table**. If you add a column to a model later (like `current_rate` was
added after `utility_types` already existed), you have to run the `ALTER TABLE` yourself:

```sql
ALTER TABLE utility_types ADD COLUMN current_rate FLOAT;
```

Once the schema stabilizes, replace `create_all()` with [Alembic](https://alembic.sqlalchemy.org/)
migrations so schema changes are generated and applied automatically instead of by hand.

## Step 9 — Seed data (`scripts/seed_utility_types.py`)

A standalone script — not an API endpoint — that inserts the four standard utility categories once:

```python
from app.core.db import Base, SessionLocal, engine
from app.models import UtilityType

DEFAULT_UTILITY_TYPES = [
    {"name": "water", "unit": "m3"},
    {"name": "energy", "unit": "kWh"},
    {"name": "gas", "unit": "m3"},
    {"name": "rent", "unit": "PLN"},
]

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for entry in DEFAULT_UTILITY_TYPES:
            if db.query(UtilityType).filter_by(name=entry["name"]).first():
                continue
            db.add(UtilityType(**entry))
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
```

Idempotent (skips entries that already exist), so it's safe to run more than once. This is also the
template for a future Google Sheets → Postgres migration script: same pattern of open a session,
loop, insert.

## Step 10 — Run it

```bash
cd backend
cp .env.example .env          # then edit .env with your real DATABASE_URL
uv run uvicorn app.main:app --reload
```

Check `http://localhost:8000/health`, then `http://localhost:8000/docs` for the interactive Swagger
UI — the fastest way to try `POST /properties`, `POST /utility-types`, `POST /usage`, and
`GET /usage/summary` by hand before wiring up the Streamlit frontend.

Seed the utility types once:

```bash
python -m scripts.seed_utility_types
```

## Extending it yourself

New resource → new file in `app/routers/` + model in `app/models.py` + schemas in `app/schemas.py` →
register the router in `app/main.py`. Each router only imports from `core` and the shared
`models`/`schemas` — never from another router — so adding a resource never requires touching
existing files.
