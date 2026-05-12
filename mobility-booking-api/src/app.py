"""
app.py – Flask REST API for the mobility booking platform.

Endpoints:
  GET  /api/v1/vehicles               – list available vehicles
  POST /api/v1/customers              – register customer
  GET  /api/v1/customers/<id>         – get customer
  POST /api/v1/bookings               – create booking
  GET  /api/v1/bookings/<id>          – get booking summary
  POST /api/v1/bookings/<id>/confirm  – confirm booking
  POST /api/v1/bookings/<id>/cancel   – cancel booking
  POST /api/v1/bookings/<id>/checkin/start    – start mobile check-in
  POST /api/v1/bookings/<id>/checkin/complete – complete mobile check-in
  POST /api/v1/assistant              – AI booking assistant query
  GET  /api/v1/health                 – health check
"""

from flask import Flask, request, jsonify
from src.store import BookingStore
from src.models import Customer, BookingStatus
from src.booking_service import BookingService, BookingError
from src.ai_assistant import AIAssistant


def create_app(dry_run: bool = True) -> Flask:
    app = Flask(__name__)
    store   = BookingStore()
    service = BookingService(store)
    ai      = AIAssistant(store, dry_run=dry_run)

    def ok(data, code=200):
        return jsonify({"status": "ok", "data": data}), code

    def err(msg, code=400):
        return jsonify({"status": "error", "message": msg}), code

    # ── Health ────────────────────────────────────────────────

    @app.route("/api/v1/health")
    def health():
        return ok({"service": "mobility-booking-api", "version": "1.0.0"})

    # ── Vehicles ──────────────────────────────────────────────

    @app.route("/api/v1/vehicles")
    def list_vehicles():
        category = request.args.get("category")
        avail    = request.args.get("available", "true").lower() == "true"
        vehicles = store.list_vehicles(available_only=avail, category=category)
        return ok([v.to_dict() for v in vehicles])

    # ── Customers ─────────────────────────────────────────────

    @app.route("/api/v1/customers", methods=["POST"])
    def create_customer():
        body = request.get_json() or {}
        required = ["first_name", "last_name", "email"]
        missing  = [f for f in required if not body.get(f)]
        if missing:
            return err(f"Missing fields: {missing}")

        if store.get_customer_by_email(body["email"]):
            return err("Email already registered.", 409)

        customer = Customer.create(
            first_name=body["first_name"],
            last_name=body["last_name"],
            email=body["email"],
            phone=body.get("phone", ""),
            license_no=body.get("license_no", ""),
        )
        store.add_customer(customer)
        return ok(customer.to_dict(), 201)

    @app.route("/api/v1/customers/<customer_id>")
    def get_customer(customer_id):
        customer = store.get_customer(customer_id)
        if not customer:
            return err("Customer not found.", 404)
        bookings = store.list_bookings(customer_id=customer_id)
        return ok({
            "customer": customer.to_dict(),
            "bookings": [b.to_dict() for b in bookings],
        })

    # ── Bookings ──────────────────────────────────────────────

    @app.route("/api/v1/bookings", methods=["POST"])
    def create_booking():
        body = request.get_json() or {}
        required = ["customer_id", "vehicle_id",
                    "pickup_date", "return_date", "pickup_location"]
        missing = [f for f in required if not body.get(f)]
        if missing:
            return err(f"Missing fields: {missing}")
        try:
            booking = service.create_booking(
                customer_id=body["customer_id"],
                vehicle_id=body["vehicle_id"],
                pickup_date=body["pickup_date"],
                return_date=body["return_date"],
                pickup_location=body["pickup_location"],
            )
            return ok(booking.to_dict(), 201)
        except BookingError as e:
            return err(str(e))

    @app.route("/api/v1/bookings/<booking_id>")
    def get_booking(booking_id):
        try:
            summary = service.get_booking_summary(booking_id)
            return ok(summary)
        except BookingError as e:
            return err(str(e), 404)

    @app.route("/api/v1/bookings/<booking_id>/confirm", methods=["POST"])
    def confirm_booking(booking_id):
        try:
            booking = service.confirm_booking(booking_id)
            return ok(booking.to_dict())
        except BookingError as e:
            return err(str(e))

    @app.route("/api/v1/bookings/<booking_id>/cancel", methods=["POST"])
    def cancel_booking(booking_id):
        try:
            booking = service.cancel_booking(booking_id)
            return ok(booking.to_dict())
        except BookingError as e:
            return err(str(e))

    # ── Mobile check-in ───────────────────────────────────────

    @app.route("/api/v1/bookings/<booking_id>/checkin/start", methods=["POST"])
    def start_checkin(booking_id):
        try:
            checkin = service.start_checkin(booking_id)
            return ok(checkin.to_dict(), 201)
        except BookingError as e:
            return err(str(e))

    @app.route("/api/v1/bookings/<booking_id>/checkin/complete", methods=["POST"])
    def complete_checkin(booking_id):
        body = request.get_json() or {}
        try:
            checkin, booking = service.complete_checkin(
                booking_id=booking_id,
                license_verified=body.get("license_verified", True),
                damage_noted=body.get("damage_noted", False),
                damage_notes=body.get("damage_notes", ""),
            )
            return ok({"check_in": checkin.to_dict(),
                        "booking": booking.to_dict()})
        except BookingError as e:
            return err(str(e))

    # ── AI Assistant ──────────────────────────────────────────

    @app.route("/api/v1/assistant", methods=["POST"])
    def assistant():
        body = request.get_json() or {}
        query = body.get("query", "").strip()
        if not query:
            return err("Missing 'query' field.")
        answer = ai.answer(
            query=query,
            customer_id=body.get("customer_id"),
            booking_id=body.get("booking_id"),
        )
        return ok({"query": query, "answer": answer})

    return app


if __name__ == "__main__":
    app = create_app(dry_run=True)
    app.run(debug=True, port=5000)
