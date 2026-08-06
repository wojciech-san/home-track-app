from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Property, UsageRecord, UtilityType
from app.schemas import PropertySummary, UsageRecordOut, UsageRecordUpsert, UtilitySummary

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=list[UsageRecordOut])
def list_usage(
    property_id: int | None = None,
    utility_type_id: int | None = None,
    month_from: date | None = None,
    month_to: date | None = None,
    db: Session = Depends(get_db),
):
    query = select(UsageRecord)
    if property_id is not None:
        query = query.where(UsageRecord.property_id == property_id)
    if utility_type_id is not None:
        query = query.where(UsageRecord.utility_type_id == utility_type_id)
    if month_from is not None:
        query = query.where(UsageRecord.month >= month_from)
    if month_to is not None:
        query = query.where(UsageRecord.month <= month_to)

    query = query.order_by(UsageRecord.month.desc())
    return db.scalars(query).all()


@router.post("", response_model=UsageRecordOut, status_code=200)
def upsert_usage(payload: UsageRecordUpsert, db: Session = Depends(get_db)):
    if not db.get(Property, payload.property_id):
        raise HTTPException(status_code=404, detail="Property not found")
    if not db.get(UtilityType, payload.utility_type_id):
        raise HTTPException(status_code=404, detail="Utility type not found")

    existing = db.scalar(
        select(UsageRecord).where(
            UsageRecord.property_id == payload.property_id,
            UsageRecord.utility_type_id == payload.utility_type_id,
            UsageRecord.month == payload.month,
        )
    )

    if existing:
        existing.value = payload.value
        existing.cost = payload.cost
        record = existing
    else:
        record = UsageRecord(**payload.model_dump())
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


@router.get("/summary", response_model=list[PropertySummary])
def usage_summary(
    month_from: date | None = None,
    month_to: date | None = None,
    property_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Usage grouped by property + month, with per-utility totals.
    This is the endpoint the Streamlit dashboard charts against."""

    query = select(UsageRecord)
    if property_id is not None:
        query = query.where(UsageRecord.property_id == property_id)
    if month_from is not None:
        query = query.where(UsageRecord.month >= month_from)
    if month_to is not None:
        query = query.where(UsageRecord.month <= month_to)

    records = db.scalars(query).all()

    properties = {p.id: p for p in db.scalars(select(Property)).all()}
    utility_types = {u.id: u for u in db.scalars(select(UtilityType)).all()}

    grouped: dict[tuple[int, date], list[UsageRecord]] = {}
    for r in records:
        grouped.setdefault((r.property_id, r.month), []).append(r)

    summaries: list[PropertySummary] = []
    for (prop_id, month), recs in sorted(grouped.items(), key=lambda kv: (kv[0][1], kv[0][0]), reverse=True):
        prop = properties.get(prop_id)
        if not prop:
            continue
        utilities = [
            UtilitySummary(
                utility_type_id=r.utility_type_id,
                utility_type_name=utility_types[r.utility_type_id].name,
                unit=utility_types[r.utility_type_id].unit,
                total_value=r.value,
                total_cost=r.cost or 0.0,
            )
            for r in recs
        ]
        summaries.append(
            PropertySummary(
                property_id=prop_id,
                property_name=prop.name,
                month=month,
                utilities=utilities,
            )
        )

    return summaries


@router.get("/{usage_id}", response_model=UsageRecordOut)
def get_usage(usage_id: int, db: Session = Depends(get_db)):
    record = db.get(UsageRecord, usage_id)
    if not record:
        raise HTTPException(status_code=404, detail="Usage record not found")
    return record
