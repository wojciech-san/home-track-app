# Home Track API

FastAPI backend for tracking monthly utility usage (water, energy, gas, rent) across multiple properties.

## Structure

```
backend/
├── .env.example                 → your DATABASE_URL goes here
├── requirements.txt             → pip dependencies
├── app/
│   ├── main.py                  → creates the FastAPI app, wires up routers
│   ├── models.py                → SQLAlchemy tables: Property, UtilityType, UsageRecord
│   ├── schemas.py                → Pydantic request/response shapes
│   ├── core/
│   │   ├── config.py             → reads DATABASE_URL from env/.env
│   │   └── db.py                 → engine, session, get_db() dependency
│   └── routers/
│       ├── properties.py
│       ├── utility_types.py
│       └── usage.py
└── scripts/
    └── seed_utility_types.py    → one-off script to insert water/energy/gas/rent
```

## Setup

1. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and set `DATABASE_URL` to your Postgres server
   (local or external — nothing in the code changes either way):

   ```
   cp .env.example .env
   ```

3. Start the API (tables are created automatically on startup):

   ```
   uvicorn app.main:app --reload
   ```

4. Seed the standard utility types (water, energy, gas, rent):

   ```
   python -m scripts.seed_utility_types
   ```

## Endpoints

- `GET /properties` — list properties
- `POST /properties` — create a property
- `GET /properties/{id}` — get a property
- `GET /utility-types` — list utility types
- `POST /utility-types` — create a utility type
- `GET /usage` — list usage records, filterable by `property_id`, `utility_type_id`, `month_from`, `month_to`
- `POST /usage` — upsert a usage record by `property_id` + `utility_type_id` + `month`
- `GET /usage/summary` — usage grouped by property + month, for dashboard charts
- `GET /usage/{id}` — get a usage record by id
- `GET /health` — health check

## Example requests

```bash
curl -X POST http://localhost:8000/properties \
  -H "Content-Type: application/json" \
  -d '{"name": "Downtown Apartment", "address": "123 Main St"}'

curl -X POST http://localhost:8000/usage \
  -H "Content-Type: application/json" \
  -d '{"property_id": 1, "utility_type_id": 1, "month": "2026-08-01", "value": 12.5, "cost": 45.0}'

curl http://localhost:8000/usage/summary
```

## Extending

New resource → new file in `app/routers/` + model in `app/models.py` + schemas in `app/schemas.py` →
register the router in `app/main.py`. Once the schema stabilizes, replace `Base.metadata.create_all()`
in `main.py` with Alembic migrations so schema changes are tracked and reversible.
