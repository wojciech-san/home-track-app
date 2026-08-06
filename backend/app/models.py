from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


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


class UtilityType(Base):
    __tablename__ = "utility_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # water, energy, gas, rent
    unit: Mapped[str | None] = mapped_column(String, nullable=True)  # m3, kWh, PLN, etc.

    usage_records: Mapped[list["UsageRecord"]] = relationship(
        back_populates="utility_type", cascade="all, delete-orphan"
    )


class UsageRecord(Base):
    __tablename__ = "usage_records"
    __table_args__ = (
        UniqueConstraint("property_id", "utility_type_id", "month", name="uq_usage_property_utility_month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    utility_type_id: Mapped[int] = mapped_column(ForeignKey("utility_types.id"), nullable=False)
    month: Mapped[date] = mapped_column(Date, nullable=False)  # first day of the month, e.g. 2026-08-01
    value: Mapped[float] = mapped_column(Float, nullable=False)  # usage amount (m3, kWh, ...)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)  # optional cost for that month
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    property: Mapped["Property"] = relationship(back_populates="usage_records")
    utility_type: Mapped["UtilityType"] = relationship(back_populates="usage_records")
