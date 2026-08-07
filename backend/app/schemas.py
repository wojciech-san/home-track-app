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
    current_rate: float | None = None  # price per unit, used to auto-calculate usage cost


class UtilityTypeCreate(UtilityTypeBase):
    pass


class UtilityTypeUpdate(BaseModel):
    unit: str | None = None
    current_rate: float | None = None


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


# ---------- Lease ----------

class LeaseBase(BaseModel):
    property_id: int
    tenant_name: str
    tenant_email: str | None = None
    tenant_phone: str | None = None
    monthly_rent: float
    deposit: float | None = None
    start_date: date
    end_date: date | None = None  # leave empty for an open-ended / month-to-month lease
    notes: str | None = None


class LeaseCreate(LeaseBase):
    pass


class LeaseUpdate(BaseModel):
    tenant_name: str | None = None
    tenant_email: str | None = None
    tenant_phone: str | None = None
    monthly_rent: float | None = None
    deposit: float | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None


class LeaseOut(LeaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
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
