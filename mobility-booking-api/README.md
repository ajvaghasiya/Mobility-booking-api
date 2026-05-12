# Mobility Booking API

A Python REST API for a car rental booking platform, covering the full digital experience lifecycle: vehicle search, customer registration, booking creation and management, mobile check-in, and an AI-powered customer assistant.


---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Flask REST API  (src/app.py)                           │
│                                                         │
│  Routes:                                                │
│    GET  /api/v1/vehicles          – search fleet        │
│    POST /api/v1/customers         – register customer   │
│    POST /api/v1/bookings          – create booking      │
│    POST /api/v1/bookings/:id/confirm                    │
│    POST /api/v1/bookings/:id/cancel                     │
│    POST /api/v1/bookings/:id/checkin/start              │
│    POST /api/v1/bookings/:id/checkin/complete           │
│    POST /api/v1/assistant         – AI query            │
│    GET  /api/v1/health                                  │
│                                                         │
│  BookingService  (business logic + lifecycle)           │
│    └── BookingStore (in-memory repository)              │
│    └── AIAssistant  (Claude API + dry-run mock)         │
└─────────────────────────────────────────────────────────┘
```

---

## Features

- **Full booking lifecycle** – pending → confirmed → active (check-in) → completed / cancelled
- **Mobile check-in** – two-step start + complete with licence verification and damage notes
- **Vehicle fleet** – 6 seeded vehicles across economy, compact, SUV, luxury, van categories
- **Automatic pricing** – days × daily rate calculated on booking creation
- **AI assistant** – Claude API integration answers natural-language queries with booking context injected; dry-run mock mode for testing
- **Clean layered architecture** – models → store → service → API
- **40+ pytest tests** covering models, store, service, and all API endpoints
- **GitHub Actions CI** (Python 3.11 + 3.12)

---

## Quick Start

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/mobility-booking-api.git
cd mobility-booking-api
pip install -r requirements.txt

# Run server (dry-run AI mode, no API key needed)
python -m src.app
```

---

## API Examples

```bash
# List available vehicles
curl http://localhost:5000/api/v1/vehicles

# Register a customer
curl -X POST http://localhost:5000/api/v1/customers \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Anna","last_name":"Müller","email":"anna@example.com","license_no":"DE123"}'

# Create a booking
curl -X POST http://localhost:5000/api/v1/bookings \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"<id>","vehicle_id":"v001","pickup_date":"2026-07-01","return_date":"2026-07-05","pickup_location":"Munich Airport"}'

# Mobile check-in
curl -X POST http://localhost:5000/api/v1/bookings/<id>/checkin/start
curl -X POST http://localhost:5000/api/v1/bookings/<id>/checkin/complete \
  -d '{"license_verified":true,"damage_noted":false}'

# AI assistant
curl -X POST http://localhost:5000/api/v1/assistant \
  -H "Content-Type: application/json" \
  -d '{"query":"Where do I pick up my car?","booking_id":"<id>"}'
```

---

## Running Tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Project Structure

```
mobility-booking-api/
├── src/
│   ├── models.py          # Customer, Vehicle, Booking, CheckIn dataclasses + enums
│   ├── store.py           # In-memory repository (seeded vehicle fleet)
│   ├── booking_service.py # Business logic: create, confirm, cancel, check-in, pricing
│   ├── ai_assistant.py    # Claude API integration with booking context + mock mode
│   └── app.py             # Flask REST API (10 endpoints)
├── tests/
│   └── test_api.py        # 40+ pytest tests (models, store, service, API)
├── .github/workflows/ci.yml
├── requirements.txt
├── upload_to_github.sh
└── README.md
```

---

## Skills Demonstrated

- **Python** REST API with Flask – clean route structure, JSON responses, error handling
- **Layered architecture** – models → repository → service → API
- **Booking lifecycle management** – state machine (pending/confirmed/active/completed/cancelled)
- **AI integration** – Anthropic Claude API with context injection and dry-run mode
- **Mobile check-in flow** – two-step API with licence verification and damage tracking
- **Testing** – 40+ pytest tests including full API endpoint coverage via Flask test client
- **CI/CD** – GitHub Actions (Python 3.11 + 3.12)

---

## License

MIT License
