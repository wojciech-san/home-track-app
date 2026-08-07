from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Lease, Property
from app.schemas import LeaseCreate, LeaseOut, LeaseUpdate

router = APIRouter(prefix="/leases", tags=["leases"])


@router.get("", response_model=list[LeaseOut])
def list_leases(
    property_id: int | None = None,
    active_on: date | None = None,
    db: Session = Depends(get_db),
):
    """List leases, optionally filtered by property, or by a date that must
    fall within [start_date, end_date] (end_date NULL counts as ongoing)."""

    query = select(Lease)
    if property_id is not None:
        query = query.where(Lease.property_id == property_id)
    if active_on is not None:
        query = query.where(
            Lease.start_date <= active_on,
            (Lease.end_date.is_(None)) | (Lease.end_date >= active_on),
        )

    query = query.order_by(Lease.start_date.desc())
    return db.scalars(query).all()


@router.post("", response_model=LeaseOut, status_code=201)
def create_lease(payload: LeaseCreate, db: Session = Depends(get_db)):
    if not db.get(Property, payload.property_id):
        raise HTTPException(status_code=404, detail="Property not found")
    if payload.end_date is not None and payload.end_date < payload.start_date:
        raise HTTPException(status_code=422, detail="end_date cannot be before start_date")

    lease = Lease(**payload.model_dump())
    db.add(lease)
    db.commit()
    db.refresh(lease)
    return lease


@router.get("/{lease_id}", response_model=LeaseOut)
def get_lease(lease_id: int, db: Session = Depends(get_db)):
    lease = db.get(Lease, lease_id)
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    return lease


@router.patch("/{lease_id}", response_model=LeaseOut)
def update_lease(lease_id: int, payload: LeaseUpdate, db: Session = Depends(get_db)):
    lease = db.get(Lease, lease_id)
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    updates = payload.model_dump(exclude_unset=True)
    new_start = updates.get("start_date", lease.start_date)
    new_end = updates.get("end_date", lease.end_date)
    if new_end is not None and new_end < new_start:
        raise HTTPException(status_code=422, detail="end_date cannot be before start_date")

    for field, value in updates.items():
        setattr(lease, field, value)

    db.commit()
    db.refresh(lease)
    return lease


@router.delete("/{lease_id}", status_code=204)
def delete_lease(lease_id: int, db: Session = Depends(get_db)):
    lease = db.get(Lease, lease_id)
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    db.delete(lease)
    db.commit()
