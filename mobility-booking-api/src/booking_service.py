"""
booking_service.py – Business logic for the booking lifecycle.
Handles create, confirm, modify, cancel, and pricing calculations.
"""

from datetime import datetime
from typing import Optional, Tuple, List
from src.models import (
    Booking, Customer, Vehicle, BookingStatus,
    CheckIn, CheckInStatus
)
from src.store import BookingStore


class BookingError(Exception):
    pass


class BookingService:
    """
    Orchestrates the booking lifecycle:
      create → confirm → activate (check-in) → complete / cancel
    """

    def __init__(self, store: BookingStore) -> None:
        self._store = store

    # ── Create ────────────────────────────────────────────────

    def create_booking(
        self,
        customer_id:     str,
        vehicle_id:      str,
        pickup_date:     str,
        return_date:     str,
        pickup_location: str,
    ) -> Booking:
        customer = self._store.get_customer(customer_id)
        if not customer:
            raise BookingError(f"Customer not found: {customer_id}")

        vehicle = self._store.get_vehicle(vehicle_id)
        if not vehicle:
            raise BookingError(f"Vehicle not found: {vehicle_id}")

        if not vehicle.available:
            raise BookingError(
                f"Vehicle {vehicle_id} is not available.")

        days  = self._calculate_days(pickup_date, return_date)
        price = round(days * vehicle.daily_rate, 2)

        booking = Booking.create(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            pickup_date=pickup_date,
            return_date=return_date,
            pickup_location=pickup_location,
            total_price=price,
        )

        self._store.add_booking(booking)
        self._store.set_vehicle_availability(vehicle_id, False)
        return booking

    # ── Confirm ───────────────────────────────────────────────

    def confirm_booking(self, booking_id: str) -> Booking:
        booking = self._get_or_raise(booking_id)
        if booking.status != BookingStatus.PENDING:
            raise BookingError(
                f"Booking {booking_id} cannot be confirmed "
                f"(status: {booking.status.value}).")
        return self._store.update_booking_status(
            booking_id, BookingStatus.CONFIRMED)

    # ── Cancel ────────────────────────────────────────────────

    def cancel_booking(self, booking_id: str) -> Booking:
        booking = self._get_or_raise(booking_id)
        if booking.status in (BookingStatus.COMPLETED,
                               BookingStatus.CANCELLED):
            raise BookingError(
                f"Booking {booking_id} is already "
                f"{booking.status.value}.")
        self._store.set_vehicle_availability(booking.vehicle_id, True)
        return self._store.update_booking_status(
            booking_id, BookingStatus.CANCELLED)

    # ── Mobile check-in ───────────────────────────────────────

    def start_checkin(self, booking_id: str) -> CheckIn:
        booking = self._get_or_raise(booking_id)
        if booking.status not in (BookingStatus.CONFIRMED,
                                   BookingStatus.PENDING):
            raise BookingError(
                f"Check-in not available for booking "
                f"status: {booking.status.value}.")

        existing = self._store.get_checkin(booking_id)
        if existing and existing.status == CheckInStatus.COMPLETED:
            raise BookingError("Check-in already completed.")

        checkin = CheckIn(
            booking_id=booking_id,
            customer_id=booking.customer_id,
            status=CheckInStatus.IN_PROGRESS,
        )
        self._store.add_checkin(checkin)
        return checkin

    def complete_checkin(
        self,
        booking_id:       str,
        license_verified: bool = True,
        damage_noted:     bool = False,
        damage_notes:     str  = "",
    ) -> Tuple[CheckIn, Booking]:
        checkin = self._store.get_checkin(booking_id)
        if not checkin:
            raise BookingError(
                f"No check-in in progress for booking {booking_id}.")
        if checkin.status == CheckInStatus.COMPLETED:
            raise BookingError("Check-in already completed.")

        checkin.license_verified = license_verified
        checkin.damage_noted     = damage_noted
        checkin.damage_notes     = damage_notes
        checkin.status           = CheckInStatus.COMPLETED
        checkin.completed_at     = datetime.utcnow().isoformat()

        booking = self._store.update_booking_status(
            booking_id, BookingStatus.ACTIVE)
        booking.check_in_status = CheckInStatus.COMPLETED

        return checkin, booking

    # ── Helpers ───────────────────────────────────────────────

    def get_booking_summary(self, booking_id: str) -> dict:
        booking  = self._get_or_raise(booking_id)
        customer = self._store.get_customer(booking.customer_id)
        vehicle  = self._store.get_vehicle(booking.vehicle_id)
        checkin  = self._store.get_checkin(booking_id)

        return {
            "booking":  booking.to_dict(),
            "customer": customer.to_dict() if customer else None,
            "vehicle":  vehicle.to_dict()  if vehicle  else None,
            "check_in": checkin.to_dict()  if checkin  else None,
        }

    def _get_or_raise(self, booking_id: str) -> Booking:
        booking = self._store.get_booking(booking_id)
        if not booking:
            raise BookingError(f"Booking not found: {booking_id}")
        return booking

    @staticmethod
    def _calculate_days(pickup: str, return_: str) -> int:
        fmt = "%Y-%m-%d"
        try:
            d1 = datetime.strptime(pickup,  fmt)
            d2 = datetime.strptime(return_, fmt)
            days = (d2 - d1).days
            return max(days, 1)
        except ValueError:
            return 1
