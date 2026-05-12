"""
models.py – Data models for the mobility booking platform.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from datetime import datetime
import uuid


class BookingStatus(Enum):
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    ACTIVE    = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VehicleCategory(Enum):
    ECONOMY   = "economy"
    COMPACT   = "compact"
    SUV       = "suv"
    LUXURY    = "luxury"
    VAN       = "van"


class CheckInStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"


@dataclass
class Customer:
    id:           str
    first_name:   str
    last_name:    str
    email:        str
    phone:        str = ""
    license_no:   str = ""
    created_at:   str = ""

    @classmethod
    def create(cls, first_name, last_name, email, phone="", license_no=""):
        return cls(
            id=str(uuid.uuid4())[:8],
            first_name=first_name, last_name=last_name,
            email=email, phone=phone, license_no=license_no,
            created_at=datetime.utcnow().isoformat(),
        )

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> dict:
        return {
            "id": self.id, "first_name": self.first_name,
            "last_name": self.last_name, "email": self.email,
            "phone": self.phone, "license_no": self.license_no,
            "created_at": self.created_at,
        }


@dataclass
class Vehicle:
    id:           str
    make:         str
    model:        str
    category:     VehicleCategory
    year:         int
    plate:        str
    daily_rate:   float
    available:    bool = True
    location:     str  = "Munich Airport"

    def to_dict(self) -> dict:
        return {
            "id": self.id, "make": self.make, "model": self.model,
            "category": self.category.value, "year": self.year,
            "plate": self.plate, "daily_rate": self.daily_rate,
            "available": self.available, "location": self.location,
        }


@dataclass
class Booking:
    id:              str
    customer_id:     str
    vehicle_id:      str
    pickup_date:     str
    return_date:     str
    pickup_location: str
    status:          BookingStatus   = BookingStatus.PENDING
    total_price:     float           = 0.0
    check_in_status: CheckInStatus   = CheckInStatus.NOT_STARTED
    created_at:      str             = ""
    notes:           str             = ""

    @classmethod
    def create(cls, customer_id, vehicle_id, pickup_date,
               return_date, pickup_location, total_price=0.0):
        return cls(
            id=str(uuid.uuid4())[:8],
            customer_id=customer_id, vehicle_id=vehicle_id,
            pickup_date=pickup_date, return_date=return_date,
            pickup_location=pickup_location,
            total_price=total_price,
            created_at=datetime.utcnow().isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "customer_id": self.customer_id,
            "vehicle_id": self.vehicle_id,
            "pickup_date": self.pickup_date,
            "return_date": self.return_date,
            "pickup_location": self.pickup_location,
            "status": self.status.value,
            "total_price": self.total_price,
            "check_in_status": self.check_in_status.value,
            "created_at": self.created_at,
            "notes": self.notes,
        }


@dataclass
class CheckIn:
    booking_id:    str
    customer_id:   str
    status:        CheckInStatus = CheckInStatus.NOT_STARTED
    license_verified: bool = False
    damage_noted:  bool   = False
    damage_notes:  str    = ""
    completed_at:  str    = ""

    def to_dict(self) -> dict:
        return {
            "booking_id": self.booking_id,
            "customer_id": self.customer_id,
            "status": self.status.value,
            "license_verified": self.license_verified,
            "damage_noted": self.damage_noted,
            "damage_notes": self.damage_notes,
            "completed_at": self.completed_at,
        }
