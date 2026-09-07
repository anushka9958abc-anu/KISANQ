import enum
from datetime import datetime, date, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)


from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def enum_col(enum_cls, **kwargs):
    return SAEnum(enum_cls, native_enum=False, values_callable=lambda x: [e.value for e in x], **kwargs)


class UserRole(str, enum.Enum):
    farmer = "farmer"
    officer = "officer"
    admin = "admin"


class CrowdLevel(str, enum.Enum):
    low = "low"
    moderate = "moderate"
    high = "high"


class ProcurementStatus(str, enum.Enum):
    registered = "registered"
    slot_assigned = "slot_assigned"
    arrived = "arrived"
    weighing = "weighing"
    quality_check = "quality_check"
    procurement_completed = "procurement_completed"
    payment_initiated = "payment_initiated"
    paid = "paid"


STATUS_FLOW = [
    ProcurementStatus.registered,
    ProcurementStatus.slot_assigned,
    ProcurementStatus.arrived,
    ProcurementStatus.weighing,
    ProcurementStatus.quality_check,
    ProcurementStatus.procurement_completed,
    ProcurementStatus.payment_initiated,
    ProcurementStatus.paid,
]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(enum_col(UserRole), default=UserRole.farmer)
    village: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    procurements = relationship("Procurement", back_populates="farmer")


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    name_hi: Mapped[str] = mapped_column(String(80))
    base_minutes: Mapped[int] = mapped_column(Integer, default=8)
    minutes_per_quintal: Mapped[float] = mapped_column(Float, default=0.6)
    season: Mapped[str] = mapped_column(String(40), default="rabi")


class Centre(Base):
    __tablename__ = "centres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    address: Mapped[str] = mapped_column(Text)
    district: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80), default="Haryana")
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    daily_capacity_quintals: Mapped[int] = mapped_column(Integer, default=2000)
    farmers_per_slot: Mapped[int] = mapped_column(Integer, default=8)
    processing_bays: Mapped[int] = mapped_column(Integer, default=4)
    open_time: Mapped[time] = mapped_column(Time, default=time(8, 0))
    close_time: Mapped[time] = mapped_column(Time, default=time(17, 0))
    slot_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    slots = relationship("Slot", back_populates="centre")


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (UniqueConstraint("centre_id", "slot_date", "start_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    centre_id: Mapped[int] = mapped_column(ForeignKey("centres.id"))
    slot_date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    max_farmers: Mapped[int] = mapped_column(Integer)
    booked_count: Mapped[int] = mapped_column(Integer, default=0)
    reserved_minutes: Mapped[int] = mapped_column(Integer, default=0)
    max_minutes: Mapped[int] = mapped_column(Integer)

    centre = relationship("Centre", back_populates="slots")
    procurements = relationship("Procurement", back_populates="slot")


class Procurement(Base):
    __tablename__ = "procurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_number: Mapped[int] = mapped_column(Integer, index=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    centre_id: Mapped[int] = mapped_column(ForeignKey("centres.id"))
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"))
    slot_id: Mapped[int | None] = mapped_column(ForeignKey("slots.id"), nullable=True)
    quantity_quintals: Mapped[float] = mapped_column(Float)
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[ProcurementStatus] = mapped_column(
        enum_col(ProcurementStatus), default=ProcurementStatus.registered
    )
    qr_code: Mapped[str] = mapped_column(String(64), unique=True)
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    farmer = relationship("User", back_populates="procurements")
    centre = relationship("Centre")
    crop = relationship("Crop")
    slot = relationship("Slot", back_populates="procurements")
    events = relationship("StatusEvent", back_populates="procurement", order_by="StatusEvent.created_at")


class StatusEvent(Base):
    __tablename__ = "status_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    procurement_id: Mapped[int] = mapped_column(ForeignKey("procurements.id"))
    status: Mapped[ProcurementStatus] = mapped_column(enum_col(ProcurementStatus))
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    procurement = relationship("Procurement", back_populates="events")


class HistoricalStat(Base):
    __tablename__ = "historical_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    centre_id: Mapped[int] = mapped_column(ForeignKey("centres.id"))
    weekday: Mapped[int] = mapped_column(Integer)
    expected_farmers: Mapped[int] = mapped_column(Integer)
    expected_quintals: Mapped[int] = mapped_column(Integer)
    avg_wait_minutes: Mapped[int] = mapped_column(Integer)
