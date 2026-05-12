"""
ai_assistant.py
===============
Agentic AI booking assistant powered by the Anthropic Claude API.

Answers natural-language queries about bookings, vehicles, and
customer accounts. Uses the current store state as context.

Supports dry-run / simulate mode for testing without API key.
"""

import json
import urllib.request
import urllib.error
from typing import Optional
from src.store import BookingStore


SYSTEM_PROMPT = """You are a helpful customer service assistant for a car rental platform.
You have access to booking, customer, and vehicle data provided in the user message.
Answer questions concisely and helpfully. If information is not in the provided data,
say so clearly. Always be polite and professional."""

MOCK_RESPONSES = {
    "booking":  "Your booking is confirmed. Pick-up is scheduled at Munich Airport.",
    "vehicle":  "We have economy, compact, SUV, luxury, and van categories available.",
    "cancel":   "I can help you cancel your booking. Please confirm your booking ID.",
    "checkin":  "Mobile check-in is available. Please verify your driving licence.",
    "price":    "Pricing depends on vehicle category and rental duration.",
    "default":  "Thank you for contacting SIXT. How can I assist you today?",
}


class AIAssistant:
    """
    Answers customer queries using Claude with booking context injected.
    """

    def __init__(
        self,
        store:     BookingStore,
        model:     str  = "claude-sonnet-4-20250514",
        dry_run:   bool = True,
        max_tokens: int = 512,
    ) -> None:
        self._store      = store
        self._model      = model
        self._dry_run    = dry_run
        self._max_tokens = max_tokens

    def answer(
        self,
        query:       str,
        customer_id: Optional[str] = None,
        booking_id:  Optional[str] = None,
    ) -> str:
        """
        Answer a natural-language customer query.
        Injects relevant booking/customer context into the prompt.
        """
        context = self._build_context(customer_id, booking_id)
        user_message = f"Context:\n{context}\n\nCustomer query: {query}"

        if self._dry_run:
            return self._mock_answer(query)

        return self._call_api(user_message)

    # ── Context builder ───────────────────────────────────────

    def _build_context(
        self,
        customer_id: Optional[str],
        booking_id:  Optional[str],
    ) -> str:
        parts = []

        if customer_id:
            customer = self._store.get_customer(customer_id)
            if customer:
                parts.append(f"Customer: {customer.full_name()} "
                             f"({customer.email})")

        if booking_id:
            booking = self._store.get_booking(booking_id)
            if booking:
                vehicle = self._store.get_vehicle(booking.vehicle_id)
                parts.append(
                    f"Booking {booking.id}: "
                    f"status={booking.status.value}, "
                    f"pickup={booking.pickup_date}, "
                    f"return={booking.return_date}, "
                    f"vehicle={vehicle.make + ' ' + vehicle.model if vehicle else 'N/A'}, "
                    f"price=€{booking.total_price}"
                )

        avail = self._store.list_vehicles(available_only=True)
        parts.append(f"Available vehicles: {len(avail)} "
                     f"({', '.join(v.category.value for v in avail[:3])}...)")

        return "\n".join(parts) if parts else "No specific context."

    # ── API call ──────────────────────────────────────────────

    def _call_api(self, user_message: str) -> str:
        payload = json.dumps({
            "model":      self._model,
            "max_tokens": self._max_tokens,
            "system":     SYSTEM_PROMPT,
            "messages":   [{"role": "user", "content": user_message}],
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type":      "application/json",
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"API error: {e.code} – {e.read().decode()}") from e

        return "".join(
            block["text"]
            for block in body.get("content", [])
            if block.get("type") == "text"
        )

    # ── Mock answers ──────────────────────────────────────────

    def _mock_answer(self, query: str) -> str:
        q = query.lower()
        for key, resp in MOCK_RESPONSES.items():
            if key in q:
                return f"[mock] {resp}"
        return f"[mock] {MOCK_RESPONSES['default']}"
