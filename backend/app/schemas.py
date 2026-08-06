from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


# ---------- Property ----------

class PropertyBase(BaseModel):
    name: str
    address: str | None = None
    notes: str | None = None


class PropertyCreate(PropertyBase):
    pass


class PropertyOut(PropertyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ---------- UtilityType ----------

class UtilityTypeBase(BaseModel):
    name: str
    unit: str | None = None


class UtilityTypeCreate(UtilityTypeBase):
    pass


class UtilityTypeOut(UtilityTypeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ---------- UsageRecord ----------

class UsageRecordUpsert(BaseModel):
    """Body for POST /usage — creates a record, or updates it if one already
    exists for the same property + utility type + month."""

    property_id: int
    utility_type_id: int
    month: date
    value: float
    cost: float | None = None


class UsageRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    property_id: int
    utility_type_id: int
    month: date
    value: float
    cost: float | None
    created_at: datetime
    updated_at: datetime


# ---------- Summary (for the dashboard) ----------

class UtilitySummary(BaseModel):
    utility_type_id: int
    utility_type_name: str
    unit: str | None
    total_value: float
    total_cost: float


class PropertySummary(BaseModel):
    property_id: int
    property_name: str
    month: date
    utilities: list[UtilitySummary]
