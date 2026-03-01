from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.services.data_service import DataService, DataServiceError
from app.billing.stripe_client import StripeClient, StripeClientError


class SubscriptionServiceError(Exception):
    pass


class SubscriptionService:

    def __init__(self, data_service: DataService):
        self._ds = data_service
        self._stripe = StripeClient()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    def create_checkout_session(self, user_id: str, price_id: str) -> Dict[str, Any]:
        user = self._ds.get_user(user_id)
        if not user:
            raise SubscriptionServiceError("User not found")

        # Create or reuse Stripe customer
        stripe_customer_id = None
        existing_sub = self._ds.get_subscription_by_user_id(user_id)
        if existing_sub:
            stripe_customer_id = existing_sub["stripe_customer_id"]
        else:
            try:
                customer = self._stripe.create_customer(
                    email=user["email"],
                    metadata={"user_id": user_id},
                )
                stripe_customer_id = customer["id"]
            except StripeClientError as exc:
                raise SubscriptionServiceError(str(exc)) from exc

        try:
            session = self._stripe.create_checkout_session(
                customer_id=stripe_customer_id,
                price_id=price_id,
            )
            return session
        except StripeClientError as exc:
            raise SubscriptionServiceError(str(exc)) from exc

    def handle_subscription_created(
        self,
        user_id: str,
        stripe_customer_id: str,
        stripe_subscription_id: str,
        status: str,
        current_period_end: Optional[int],
        cancel_at_period_end: bool,
    ) -> Dict[str, Any]:

        period_end_iso = None
        if current_period_end:
            period_end_iso = datetime.fromtimestamp(
                current_period_end, tz=timezone.utc
            ).isoformat()

        existing = self._ds.get_subscription_by_user_id(user_id)

        if existing:
            return self._ds.update_subscription(
                existing["subscription_id"],
                {
                    "stripe_subscription_id": stripe_subscription_id,
                    "status": status,
                    "current_period_end": period_end_iso,
                    "cancel_at_period_end": cancel_at_period_end,
                },
            )

        return self._ds.create_subscription(
            {
                "user_id": user_id,
                "stripe_customer_id": stripe_customer_id,
                "stripe_subscription_id": stripe_subscription_id,
                "status": status,
                "current_period_end": period_end_iso,
                "cancel_at_period_end": cancel_at_period_end,
            }
        )

    def cancel_subscription(self, user_id: str) -> Dict[str, Any]:
        sub = self._ds.get_subscription_by_user_id(user_id)
        if not sub:
            raise SubscriptionServiceError("Subscription not found")

        try:
            self._stripe.cancel_subscription(
                sub["stripe_subscription_id"]
            )
        except StripeClientError as exc:
            raise SubscriptionServiceError(str(exc)) from exc

        return self._ds.update_subscription(
            sub["subscription_id"],
            {"cancel_at_period_end": True},
        )