from __future__ import annotations

from typing import Dict, Any

from app.billing.stripe_client import StripeClient, StripeWebhookError
from app.billing.subscription_service import SubscriptionService
from app.services.data_service import DataService


class WebhookProcessorError(Exception):
    pass


class WebhookProcessor:

    def __init__(self, data_service: DataService):
        self._stripe = StripeClient()
        self._subs = SubscriptionService(data_service)

    # ──────────────────────────────────────────────────────────────
    # Entry point
    # ──────────────────────────────────────────────────────────────

    def process(self, body: bytes, sig_header: str) -> Dict[str, Any]:
        try:
            event = self._stripe.construct_webhook_event(
                body=body,
                sig_header=sig_header,
            )
        except StripeWebhookError as exc:
            raise WebhookProcessorError(str(exc)) from exc

        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            return self._handle_checkout_completed(data)

        if event_type == "customer.subscription.updated":
            return self._handle_subscription_updated(data)

        if event_type == "customer.subscription.deleted":
            return self._handle_subscription_deleted(data)

        return {"ignored": event_type}

    # ──────────────────────────────────────────────────────────────
    # Handlers
    # ──────────────────────────────────────────────────────────────

    def _handle_checkout_completed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if data.get("mode") != "subscription":
            return {"ignored": "not_subscription_checkout"}

        user_id = data["metadata"]["user_id"]
        stripe_customer_id = data["customer"]
        stripe_subscription_id = data["subscription"]

        return {
            "event": "checkout_completed",
            "user_id": user_id,
            "stripe_subscription_id": stripe_subscription_id,
        }

    def _handle_subscription_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event": "subscription_updated",
            "stripe_subscription_id": data["id"],
            "status": data["status"],
        }

    def _handle_subscription_deleted(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event": "subscription_deleted",
            "stripe_subscription_id": data["id"],
        }