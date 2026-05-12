"""
Pytest test suite for mobility-booking-api.
Run: pytest tests/ -v
"""

import pytest
import json
from src.models import (
    Customer, Vehicle, Booking, CheckIn,
    BookingStatus, VehicleCategory, CheckInStatus
)
from src.store import BookingStore
from src.booking_service import BookingService, BookingError
from src.ai_assistant import AIAssistant
from src.app import create_app


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def store():
    return BookingStore()

@pytest.fixture
def service(store):
    return BookingService(store)

@pytest.fixture
def customer(store):
    c = Customer.create("Anna", "Müller", "anna@example.com",
                        phone="+49123456789", license_no="DE123456")
    store.add_customer(c)
    return c

@pytest.fixture
def booking(store, service, customer):
    return service.create_booking(
        customer_id=customer.id,
        vehicle_id="v001",
        pickup_date="2026-07-01",
        return_date="2026-07-05",
        pickup_location="Munich Airport",
    )

@pytest.fixture
def app_client():
    app = create_app(dry_run=True)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def ai(store):
    return AIAssistant(store, dry_run=True)


# ── Customer model tests ──────────────────────────────────────

class TestCustomer:

    def test_create_generates_id(self):
        c = Customer.create("Max", "Muster", "max@example.com")
        assert c.id
        assert len(c.id) == 8

    def test_full_name(self):
        c = Customer.create("Max", "Muster", "max@example.com")
        assert c.full_name() == "Max Muster"

    def test_to_dict_has_all_fields(self):
        c = Customer.create("Max", "Muster", "max@example.com")
        d = c.to_dict()
        for key in ("id", "first_name", "last_name", "email", "created_at"):
            assert key in d

    def test_created_at_populated(self):
        c = Customer.create("Max", "Muster", "max@example.com")
        assert c.created_at != ""


# ── BookingStore tests ────────────────────────────────────────

class TestBookingStore:

    def test_seed_vehicles_loaded(self, store):
        vehicles = store.list_vehicles()
        assert len(vehicles) >= 6

    def test_available_vehicles_filter(self, store):
        avail = store.list_vehicles(available_only=True)
        assert all(v.available for v in avail)

    def test_category_filter(self, store):
        suvs = store.list_vehicles(category="suv")
        assert all(v.category == VehicleCategory.SUV for v in suvs)

    def test_add_and_get_customer(self, store):
        c = Customer.create("Test", "User", "test@example.com")
        store.add_customer(c)
        assert store.get_customer(c.id) == c

    def test_get_customer_by_email(self, store):
        c = Customer.create("Test", "User", "unique@example.com")
        store.add_customer(c)
        found = store.get_customer_by_email("unique@example.com")
        assert found is not None
        assert found.id == c.id

    def test_get_missing_customer_returns_none(self, store):
        assert store.get_customer("nonexistent") is None

    def test_vehicle_availability_toggle(self, store):
        store.set_vehicle_availability("v001", False)
        v = store.get_vehicle("v001")
        assert not v.available
        store.set_vehicle_availability("v001", True)
        assert store.get_vehicle("v001").available

    def test_list_bookings_by_customer(self, store, service, customer):
        service.create_booking(customer.id, "v001",
                               "2026-07-01", "2026-07-03", "Munich")
        bookings = store.list_bookings(customer_id=customer.id)
        assert len(bookings) == 1

    def test_list_bookings_by_status(self, store, service, customer):
        b = service.create_booking(customer.id, "v002",
                                   "2026-07-01", "2026-07-03", "Munich")
        service.confirm_booking(b.id)
        confirmed = store.list_bookings(status="confirmed")
        assert any(bk.id == b.id for bk in confirmed)


# ── BookingService tests ──────────────────────────────────────

class TestBookingService:

    def test_create_booking_success(self, booking):
        assert booking.id
        assert booking.status == BookingStatus.PENDING
        assert booking.total_price > 0

    def test_create_booking_calculates_price(self, booking):
        # 4 days * €49/day = €196
        assert booking.total_price == 196.0

    def test_create_booking_marks_vehicle_unavailable(self, store, booking):
        v = store.get_vehicle("v001")
        assert not v.available

    def test_create_booking_invalid_customer(self, service):
        with pytest.raises(BookingError, match="Customer not found"):
            service.create_booking("bad-id", "v001",
                                   "2026-07-01", "2026-07-02", "Munich")

    def test_create_booking_invalid_vehicle(self, service, customer):
        with pytest.raises(BookingError, match="Vehicle not found"):
            service.create_booking(customer.id, "bad-v",
                                   "2026-07-01", "2026-07-02", "Munich")

    def test_create_booking_unavailable_vehicle(self, service, customer, booking):
        with pytest.raises(BookingError, match="not available"):
            service.create_booking(customer.id, "v001",
                                   "2026-07-10", "2026-07-12", "Munich")

    def test_confirm_booking(self, service, booking):
        confirmed = service.confirm_booking(booking.id)
        assert confirmed.status == BookingStatus.CONFIRMED

    def test_confirm_already_confirmed_raises(self, service, booking):
        service.confirm_booking(booking.id)
        with pytest.raises(BookingError, match="cannot be confirmed"):
            service.confirm_booking(booking.id)

    def test_cancel_booking(self, service, store, booking):
        cancelled = service.cancel_booking(booking.id)
        assert cancelled.status == BookingStatus.CANCELLED
        assert store.get_vehicle("v001").available

    def test_cancel_already_cancelled_raises(self, service, booking):
        service.cancel_booking(booking.id)
        with pytest.raises(BookingError, match="already cancelled"):
            service.cancel_booking(booking.id)

    def test_cancel_nonexistent_raises(self, service):
        with pytest.raises(BookingError, match="not found"):
            service.cancel_booking("bad-id")

    def test_start_checkin(self, service, booking):
        service.confirm_booking(booking.id)
        checkin = service.start_checkin(booking.id)
        assert checkin.status == CheckInStatus.IN_PROGRESS

    def test_complete_checkin(self, service, booking):
        service.confirm_booking(booking.id)
        service.start_checkin(booking.id)
        checkin, updated_booking = service.complete_checkin(booking.id)
        assert checkin.status == CheckInStatus.COMPLETED
        assert updated_booking.status == BookingStatus.ACTIVE

    def test_complete_checkin_twice_raises(self, service, booking):
        service.confirm_booking(booking.id)
        service.start_checkin(booking.id)
        service.complete_checkin(booking.id)
        with pytest.raises(BookingError, match="already completed"):
            service.complete_checkin(booking.id)

    def test_booking_summary_structure(self, service, booking):
        summary = service.get_booking_summary(booking.id)
        assert "booking" in summary
        assert "customer" in summary
        assert "vehicle" in summary

    def test_days_calculation_min_one(self):
        assert BookingService._calculate_days(
            "2026-07-01", "2026-07-01") == 1

    def test_days_calculation_multiple(self):
        assert BookingService._calculate_days(
            "2026-07-01", "2026-07-05") == 4


# ── AIAssistant tests ─────────────────────────────────────────

class TestAIAssistant:

    def test_dry_run_returns_mock(self, ai):
        resp = ai.answer("What vehicles do you have?")
        assert "[mock]" in resp

    def test_booking_query_mock(self, ai):
        resp = ai.answer("Where is my booking?")
        assert len(resp) > 0

    def test_with_customer_context(self, ai, store, customer):
        resp = ai.answer("Check my booking status",
                         customer_id=customer.id)
        assert len(resp) > 0

    def test_with_booking_context(self, ai, store, service, customer, booking):
        resp = ai.answer("What is my total price?",
                         booking_id=booking.id)
        assert len(resp) > 0


# ── Flask API tests ───────────────────────────────────────────

class TestAPI:

    def _register_customer(self, client):
        return client.post("/api/v1/customers", json={
            "first_name": "Anna", "last_name": "Schmidt",
            "email": "anna.schmidt@example.com",
            "phone": "+4912345", "license_no": "DE999",
        })

    def test_health_endpoint(self, app_client):
        r = app_client.get("/api/v1/health")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "ok"

    def test_list_vehicles(self, app_client):
        r = app_client.get("/api/v1/vehicles")
        assert r.status_code == 200
        data = r.get_json()
        assert len(data["data"]) >= 6

    def test_list_vehicles_category_filter(self, app_client):
        r = app_client.get("/api/v1/vehicles?category=suv")
        assert r.status_code == 200
        for v in r.get_json()["data"]:
            assert v["category"] == "suv"

    def test_create_customer(self, app_client):
        r = self._register_customer(app_client)
        assert r.status_code == 201
        data = r.get_json()["data"]
        assert data["email"] == "anna.schmidt@example.com"

    def test_create_customer_duplicate_email(self, app_client):
        self._register_customer(app_client)
        r = self._register_customer(app_client)
        assert r.status_code == 409

    def test_create_customer_missing_field(self, app_client):
        r = app_client.post("/api/v1/customers",
                            json={"first_name": "Only"})
        assert r.status_code == 400

    def test_get_customer(self, app_client):
        r = self._register_customer(app_client)
        cid = r.get_json()["data"]["id"]
        r2  = app_client.get(f"/api/v1/customers/{cid}")
        assert r2.status_code == 200
        assert r2.get_json()["data"]["customer"]["id"] == cid

    def test_get_missing_customer(self, app_client):
        r = app_client.get("/api/v1/customers/nonexistent")
        assert r.status_code == 404

    def test_create_booking(self, app_client):
        cid = self._register_customer(app_client).get_json()["data"]["id"]
        r = app_client.post("/api/v1/bookings", json={
            "customer_id": cid, "vehicle_id": "v001",
            "pickup_date": "2026-07-01", "return_date": "2026-07-04",
            "pickup_location": "Munich Airport",
        })
        assert r.status_code == 201
        data = r.get_json()["data"]
        assert data["status"] == "pending"
        assert data["total_price"] > 0

    def test_confirm_booking(self, app_client):
        cid = self._register_customer(app_client).get_json()["data"]["id"]
        bid = app_client.post("/api/v1/bookings", json={
            "customer_id": cid, "vehicle_id": "v003",
            "pickup_date": "2026-07-01", "return_date": "2026-07-03",
            "pickup_location": "Munich Airport",
        }).get_json()["data"]["id"]
        r = app_client.post(f"/api/v1/bookings/{bid}/confirm")
        assert r.status_code == 200
        assert r.get_json()["data"]["status"] == "confirmed"

    def test_cancel_booking(self, app_client):
        cid = self._register_customer(app_client).get_json()["data"]["id"]
        bid = app_client.post("/api/v1/bookings", json={
            "customer_id": cid, "vehicle_id": "v004",
            "pickup_date": "2026-07-01", "return_date": "2026-07-03",
            "pickup_location": "Munich Airport",
        }).get_json()["data"]["id"]
        r = app_client.post(f"/api/v1/bookings/{bid}/cancel")
        assert r.status_code == 200
        assert r.get_json()["data"]["status"] == "cancelled"

    def test_mobile_checkin_flow(self, app_client):
        cid = self._register_customer(app_client).get_json()["data"]["id"]
        bid = app_client.post("/api/v1/bookings", json={
            "customer_id": cid, "vehicle_id": "v005",
            "pickup_date": "2026-07-01", "return_date": "2026-07-03",
            "pickup_location": "Munich Airport",
        }).get_json()["data"]["id"]
        app_client.post(f"/api/v1/bookings/{bid}/confirm")
        r1 = app_client.post(f"/api/v1/bookings/{bid}/checkin/start")
        assert r1.status_code == 201
        r2 = app_client.post(
            f"/api/v1/bookings/{bid}/checkin/complete",
            json={"license_verified": True, "damage_noted": False})
        assert r2.status_code == 200
        data = r2.get_json()["data"]
        assert data["booking"]["status"] == "active"
        assert data["check_in"]["status"] == "completed"

    def test_ai_assistant_endpoint(self, app_client):
        r = app_client.post("/api/v1/assistant",
                            json={"query": "What vehicles do you have?"})
        assert r.status_code == 200
        assert "answer" in r.get_json()["data"]

    def test_ai_assistant_missing_query(self, app_client):
        r = app_client.post("/api/v1/assistant", json={})
        assert r.status_code == 400

    def test_get_booking_summary(self, app_client):
        cid = self._register_customer(app_client).get_json()["data"]["id"]
        bid = app_client.post("/api/v1/bookings", json={
            "customer_id": cid, "vehicle_id": "v006",
            "pickup_date": "2026-07-01", "return_date": "2026-07-02",
            "pickup_location": "Munich Airport",
        }).get_json()["data"]["id"]
        r = app_client.get(f"/api/v1/bookings/{bid}")
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert "customer" in data and "vehicle" in data
