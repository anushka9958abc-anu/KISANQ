from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, Field


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    user_id: int


class RegisterIn(BaseModel):
    name: str
    phone: str
    password: str
    village: Optional[str] = None
    district: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class LoginIn(BaseModel):
    phone: str
    password: str


class TimeEstimateIn(BaseModel):
    crop_id: int
    quantity_quintals: float = Field(gt=0)


class BookSlotIn(BaseModel):
    crop_id: int
    quantity_quintals: float = Field(gt=0)
    preferred_centre_id: int
    preferred_date: date
    lat: Optional[float] = None
    lng: Optional[float] = None


class StatusAdvanceIn(BaseModel):
    note: Optional[str] = None


class IotScanIn(BaseModel):
    qr_code: str
    centre_id: int
    device_id: str = "esp32-gate-1"
