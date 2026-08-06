from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import UtilityType
from app.schemas import UtilityTypeCreate, UtilityTypeOut

router = APIRouter(prefix="/utility-types", tags=["utility-types"])


@router.get("", response_model=list[UtilityTypeOut])
def list_utility_types(db: Session = Depends(get_db)):
    return db.scalars(select(UtilityType).order_by(UtilityType.name)).all()


@router.post("", response_model=UtilityTypeOut, status_code=201)
def create_utility_type(payload: UtilityTypeCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(UtilityType).where(UtilityType.name == payload.name))
    if existing:
        raise HTTPException(status_code=409, detail="Utility type with this name already exists")

    utility_type = UtilityType(**payload.model_dump())
    db.add(utility_type)
    db.commit()
    db.refresh(utility_type)
    return utility_type
