# Home Track API

FastAPI backend for tracking monthly utility usage (water, energy, gas, rent) across multiple properties.

## Structure

```
backend/
├── .env.example                 → your DATABASE_URL goes here
├── requirements.txt             → pip dependencies
├── app/
│   ├── main.py                  → creates the FastAPI app, wires up routers
│   ├── models.py                → SQLAlchemy tables: Property, UtilityType, UsageRecord, Lease
│   ├── schemas.py                → Pydantic request/response shapes
│   ├── core/
│   │   ├── config.py             → reads DATABASE_URL from env/.env
│   │   └── db.py                 → engine, session, get_db() dependency
│   └── routers/
│       ├── properties.py
│       ├── utility_types.py
│       ├── usage.py
│       └── leases.py
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
- `POST /utility-types` — create a utility type (`current_rate` = price per unit, e.g. PLN per m3/kWh)
- `PATCH /utility-types/{id}` — update `current_rate` when your provider's price changes
- `GET /usage` — list usage records, filterable by `property_id`, `utility_type_id`, `month_from`, `month_to`
- `POST /usage` — upsert a usage record by `property_id` + `utility_type_id` + `month`. If `cost` is omitted,
  it's auto-calculated as `value * utility_type.current_rate`; pass `cost` explicitly to override (e.g. a flat bill).
- `GET /usage/summary` — usage grouped by property + month, for dashboard charts
- `GET /usage/{id}` — get a usage record by id
- `GET /leases` — list leases, filterable by `property_id`, or `active_on` (a date that must fall within the lease term)
- `POST /leases` — create a lease (tenant info, monthly rent, start/end date)
- `GET /leases/{id}` — get a lease
- `PATCH /leases/{id}` — update a lease (e.g. set `end_date` when a tenant moves out)
- `DELETE /leases/{id}` — delete a lease
- `GET /health` — health check

## Example requests

```bash
curl -X POST http://localhost:8000/properties \
  -H "Content-Type: application/json" \
  -d '{"name": "Downtown Apartment", "address": "123 Main St"}'

curl -X PATCH http://localhost:8000/utility-types/1 \
  -H "Content-Type: application/json" \
  -d '{"current_rate": 3.6}'

curl -X POST http://localhost:8000/usage \
  -H "Content-Type: application/json" \
  -d '{"property_id": 1, "utility_type_id": 1, "month": "2026-08-01", "value": 12.5}'

curl http://localhost:8000/usage/summary

curl -X POST http://localhost:8000/leases \
  -H "Content-Type: application/json" \
  -d '{"property_id": 1, "tenant_name": "Jane Doe", "tenant_email": "jane@example.com", "monthly_rent": 1200, "deposit": 1200, "start_date": "2026-08-01"}'
```

## Extending

New resource → new file in `app/routers/` + model in `app/models.py` + schemas in `app/schemas.py` →
register the router in `app/main.py`. Once the schema stabilizes, replace `Base.metadata.create_all()`
in `main.py` with Alembic migrations so schema changes are tracked and reversible.
