"""One-off script to insert the standard utility categories.

Run after the tables exist (i.e. after the API has started at least once,
or after calling Base.metadata.create_all yourself):

    python -m scripts.seed_utility_types
"""

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
            existing = db.query(UtilityType).filter_by(name=entry["name"]).first()
            if existing:
                print(f"skip (exists): {entry['name']}")
                continue
            db.add(UtilityType(**entry))
            print(f"added: {entry['name']}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
