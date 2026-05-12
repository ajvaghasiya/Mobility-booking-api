"""
store.py – In-memory data store for customers, vehicles, bookings, and check-ins.
Acts as a simple repository layer — easy to swap for a real DB later.
"""

from typing import Dict, List, Optional
from src.models import Customer, Vehicle, Booking, CheckIn, BookingStatus, VehicleCategory


class BookingStore:
    """Thread-safe in-memory store for all platform entities."""

    def __init__(self) -> None:
        self._customers:  Dict[str, Customer] = {}
        self._vehicles:   Dict[str, Vehicle]  = {}
        self._bookings:   Dict[str, Booking]  = {}
        self._checkins:   Dict[str, CheckIn]  = {}
        self._seed()

    # ── Customers ─────────────────────────────────────────────

    def add_customer(self, c: Customer) -> Customer:
        self._customers[c.id] = c
        return c

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return self._customers.get(customer_id)

    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        return next((c for c in self._customers.values()
                     if c.email == email), None)

    def list_customers(self) -> List[Customer]:
        return list(self._customers.values())

    # ── Vehicles ──────────────────────────────────────────────

    def add_vehicle(self, v: Vehicle) -> Vehicle:
        self._vehicles[v.id] = v
        return v

    def get_vehicle(self, vehicle_id: str) -> Optional[Vehicle]:
        return self._vehicles.get(vehicle_id)

    def list_vehicles(
        self,
        available_only: bool = False,
        category: Optional[str] = None,
    ) -> List[Vehicle]:
        vehicles = list(self._vehicles.values())
        if available_only:
            vehicles = [v for v in vehicles if v.available]
        if category:
            vehicles = [v for v in vehicles
                        if v.category.value == category]
        return vehicles

    def set_vehicle_availability(self, vehicle_id: str, available: bool) -> bool:
        v = self._vehicles.get(vehicle_id)
        if not v:
            return False
        v.available = available
        return True

    # ── Bookings ──────────────────────────────────────────────

    def add_booking(self, b: Booking) -> Booking:
        self._bookings[b.id] = b
        return b

    def get_booking(self, booking_id: str) -> Optional[Booking]:
        return self._bookings.get(booking_id)

    def list_bookings(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Booking]:
        bookings = list(self._bookings.values())
        if customer_id:
            bookings = [b for b in bookings
                        if b.customer_id == customer_id]
        if status:
            bookings = [b for b in bookings
                        if b.status.value == status]
        return bookings

    def update_booking_status(
        self, booking_id: str, status: BookingStatus
    ) -> Optional[Booking]:
        b = self._bookings.get(booking_id)
        if not b:
            return None
        b.status = status
        return b

    # ── Check-ins ─────────────────────────────────────────────

    def add_checkin(self, c: CheckIn) -> CheckIn:
        self._checkins[c.booking_id] = c
        return c

    def get_checkin(self, booking_id: str) -> Optional[CheckIn]:
        return self._checkins.get(booking_id)

    # ── Seed data ─────────────────────────────────────────────

    def _seed(self) -> None:
        """Populate store with sample vehicles for development."""
        from src.models import Vehicle, VehicleCategory
        vehicles = [
            Vehicle("v001", "Volkswagen", "Golf",    VehicleCategory.ECONOMY,  2023, "MUC-001", 49.0),
            Vehicle("v002", "BMW",        "3 Series",VehicleCategory.COMPACT,  2023, "MUC-002", 89.0),
            Vehicle("v003", "Mercedes",   "GLE",     VehicleCategory.SUV,      2024, "MUC-003", 149.0),
            Vehicle("v004", "Porsche",    "Cayenne", VehicleCategory.LUXURY,   2024, "MUC-004", 299.0),
            Vehicle("v005", "Ford",       "Transit", VehicleCategory.VAN,      2023, "MUC-005", 99.0),
            Vehicle("v006", "Audi",       "A3",      VehicleCategory.ECONOMY,  2022, "MUC-006", 55.0),
        ]
        for v in vehicles:
            self._vehicles[v.id] = v
