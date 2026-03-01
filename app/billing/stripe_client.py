"""
Stripe infrastructure client — Career Architect Pro.

All outbound Stripe API calls are isolated in this module.
No business logic. No domain objects. No tier rules. Pure infrastructure boundary.

SDK version: stripe-python v14+ (v1 namespace).
  All resource calls go through StripeClient.v1.* subresources.
  The webhook signature check uses the module-level stripe.Webhook.construct_event,
  which is not bound to a client instance and does not require a live API key.

Dependency-injection design:
  api_key and webhook_secret are constructor parameters that default to env vars.
  Tests pass explicit values; production uses the defaults.
  The global stripe module state (stripe.api_key) is never mutated.
"""
from __future__ import annotations

import os
from typing import Optional

import stripe


# ── Custom exceptions ─────────────────────────────────────────────────────────


class StripeConfigurationError(RuntimeError):
    """
    Raised at construction time when required environment variables are absent.
    Surfaces immediately on startup rather than at the first API call.
    """


class StripeClientError(Exception):
    """
    Raised when a Stripe API call fails (network error, card decline,
    invalid parameters, rate limit, etc.).

    Wraps stripe.StripeError so callers — SubscriptionService,
    WebhookProcessor — do not need to import the stripe package themselves.

    Attributes:
        stripe_code:  Stripe machine-readable error code, e.g. "card_declined".
                      None when the error is not API-originated (network, etc.).
        http_status:  HTTP status code from Stripe's response, or None.
    """

    def __init__(
        self,
        message: str,
        stripe_code: Optional[str] = None,
        http_status: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.stripe_code = stripe_code
        self.http_status = http_status


class StripeWebhookError(ValueError):
    """
    Raised when webhook payload verification fails: bad signature, expired
    timestamp, missing secret, or malformed JSON.

    The webhook endpoint must return HTTP 400 on this error.
    Stripe will NOT retry on 4xx responses.
    """


# ── Client ────────────────────────────────────────────────────────────────────


class StripeClient:
    """
    Thin infrastructure wrapper around the stripe-python SDK (v14+).

    Every outbound Stripe API call in the billing layer goes through this class.
    The class has no opinions about tiers, users, or business rules.

    All methods raise StripeClientError on API failures so callers do not
    need to handle stripe-specific exception types.

    Usage — production (reads env vars automatically):
        client = StripeClient()

    Usage — tests (explicit injection, no live network calls needed):
        client = StripeClient(api_key="sk_test_...", webhook_secret="whsec_...")
        # Replace with a Mock to eliminate network calls entirely.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ) -> None:
        """
        Args:
            api_key:        Stripe secret key (sk_live_* or sk_test_*).
                            Defaults to STRIPE_SECRET_KEY env var.
            webhook_secret: Stripe webhook signing secret (whsec_*).
                            Defaults to STRIPE_WEBHOOK_SECRET env var.
                            Only required by construct_webhook_event;
                            other methods work without it.

        Raises:
            StripeConfigurationError: If api_key is absent in both the
                                      argument and the environment.
        """
        resolved_key: str = api_key or os.environ.get("STRIPE_SECRET_KEY", "")
        if not resolved_key:
            raise StripeConfigurationError(
                "Stripe API key is not configured. "
                "Set the STRIPE_SECRET_KEY environment variable or pass "
                "api_key= to StripeClient()."
            )

        self._webhook_secret: str = (
            webhook_secret or os.environ.get("STRIPE_WEBHOOK_SECRET", "")
        )

        # stripe.StripeClient holds the API key on the instance.
        # The global stripe.api_key is intentionally never set.
        self._client = stripe.StripeClient(resolved_key)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _call(self, fn, *args, **kwargs):
        """
        Execute a stripe SDK call and translate stripe.StripeError →
        StripeClientError.

        Args:
            fn:      A bound method on self._client.v1.* (e.g.
                     self._client.v1.customers.create).
            *args:   Positional arguments forwarded to fn.
            **kwargs: Keyword arguments forwarded to fn.

        Returns:
            Whatever the SDK method returns (a StripeObject subclass).

        Raises:
            StripeClientError: On any stripe.StripeError.
        """
        try:
            return fn(*args, **kwargs)
        except stripe.StripeError as exc:
            raise StripeClientError(
                str(exc),
                stripe_code=getattr(exc, "code", None),
                http_status=getattr(exc, "http_status", None),
            ) from exc

    @staticmethod
    def _to_dict(stripe_object) -> dict:
        """
        Convert a StripeObject to a plain Python dict (recursive).

        Uses to_dict_recursive() when available (stripe-python v2+), falling
        back to dict() for forward compatibility if the method is ever removed.
        """
        if hasattr(stripe_object, "to_dict_recursive"):
            return stripe_object.to_dict_recursive()
        return dict(stripe_object)  # pragma: no cover — SDK contract fallback

    # ── Customer ──────────────────────────────────────────────────────────────

    def create_customer(self, email: str) -> str:
        """
        Creates a Stripe Customer record for a new subscriber.

        A Customer is created once per user and stored on the user record
        (users.stripe_customer_id). Subsequent subscriptions and portal
        sessions reference this customer ID.

        Args:
            email: User's email address. Used for Stripe invoices, receipts,
                   and the hosted billing portal.

        Returns:
            Stripe Customer ID string, e.g. "cus_Xyz123".

        Raises:
            StripeClientError: On Stripe API failure.
        """
        customer = self._call(
            self._client.v1.customers.create,
            {"email": email},
        )
        return customer.id

    # ── Checkout ──────────────────────────────────────────────────────────────

    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> dict:
        """
        Creates a Stripe Checkout Session for a new subscription.

        The caller redirects the user to the returned checkout_url. After
        successful payment Stripe fires checkout.session.completed, which
        the webhook processor uses to activate the subscription.

        Args:
            customer_id:  Stripe Customer ID (cus_...) for the subscriber.
            price_id:     Stripe Price ID to subscribe to (price_...).
                          Must be a recurring price.
            success_url:  URL Stripe redirects to after payment succeeds.
                          Embed {CHECKOUT_SESSION_ID} to read the session
                          on the return page for confirmation.
            cancel_url:   URL Stripe redirects to when the user abandons
                          the checkout form.

        Returns:
            dict with:
                session_id   (str) — Checkout Session ID, e.g. "cs_..."
                checkout_url (str) — Hosted checkout page URL

        Raises:
            StripeClientError: On Stripe API failure.
        """
        session = self._call(
            self._client.v1.checkout.sessions.create,
            {
                "customer": customer_id,
                "line_items": [{"price": price_id, "quantity": 1}],
                "mode": "subscription",
                "success_url": success_url,
                "cancel_url": cancel_url,
            },
        )
        return {"session_id": session.id, "checkout_url": session.url}

    # ── Billing portal ────────────────────────────────────────────────────────

    def create_portal_session(self, customer_id: str, return_url: str) -> dict:
        """
        Creates a Stripe Billing Portal session.

        The Stripe-hosted portal handles payment method updates, invoice
        history, plan changes, and self-service cancellation without any
        custom UI. Plan changes and cancellations made through the portal
        fire the same webhooks as API-driven changes.

        Args:
            customer_id: Stripe Customer ID (cus_...).
            return_url:  URL the user is sent to when they exit the portal.

        Returns:
            dict with:
                portal_url (str) — Hosted billing portal URL

        Raises:
            StripeClientError: On Stripe API failure.
        """
        session = self._call(
            self._client.v1.billing_portal.sessions.create,
            {
                "customer": customer_id,
                "return_url": return_url,
            },
        )
        return {"portal_url": session.url}

    # ── Subscription management ───────────────────────────────────────────────

    def retrieve_subscription(self, subscription_id: str) -> dict:
        """
        Fetches the current state of a Stripe subscription.

        Used by SubscriptionService to read status, current_period_end,
        cancel_at_period_end, and items before performing modifications.

        Args:
            subscription_id: Stripe Subscription ID (sub_...).

        Returns:
            Full subscription dict from Stripe.

        Raises:
            StripeClientError: On Stripe API failure or ID not found.
        """
        subscription = self._call(
            self._client.v1.subscriptions.retrieve,
            subscription_id,
        )
        return self._to_dict(subscription)

    def modify_subscription(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_behavior: str = "create_prorations",
    ) -> dict:
        """
        Changes the price on an active subscription (plan upgrade or downgrade).

        Retrieves the subscription first to obtain the subscription item ID,
        then updates that item to the new price in a single Stripe call.
        Stripe handles proration automatically according to proration_behavior.

        Args:
            subscription_id:    Stripe Subscription ID (sub_...).
            new_price_id:       Target Stripe Price ID (price_...).
            proration_behavior: Controls how Stripe handles the cost difference.
                                "create_prorations" — immediately credit/charge
                                    the prorated amount (use for upgrades).
                                "none"              — no proration; new price
                                    takes effect at next renewal (use for
                                    end-of-period downgrades).
                                "always_invoice"    — immediately invoice the
                                    prorated amount.

        Returns:
            Updated subscription dict from Stripe.

        Raises:
            StripeClientError: On Stripe API failure.
        """
        # Retrieve to obtain the subscription item ID.
        # The item ID is required by Stripe to update a specific line item.
        subscription = self._call(
            self._client.v1.subscriptions.retrieve,
            subscription_id,
        )
        item_id: str = subscription["items"]["data"][0]["id"]

        updated = self._call(
            self._client.v1.subscriptions.update,
            subscription_id,
            {
                "items": [{"id": item_id, "price": new_price_id}],
                "proration_behavior": proration_behavior,
            },
        )
        return self._to_dict(updated)

    def cancel_subscription(self, subscription_id: str) -> dict:
        """
        Cancels a subscription immediately.

        The subscription status becomes "canceled" at once. Stripe fires
        customer.subscription.deleted. The webhook processor downgrades the
        user to Free tier immediately upon receiving that event.

        No further invoices are generated after immediate cancellation.
        Partial-period refunds are not issued automatically; handle manually
        via the Stripe Dashboard if required.

        Args:
            subscription_id: Stripe Subscription ID (sub_...).

        Returns:
            Canceled subscription dict from Stripe (status="canceled").

        Raises:
            StripeClientError: On Stripe API failure.
        """
        canceled = self._call(
            self._client.v1.subscriptions.cancel,
            subscription_id,
        )
        return self._to_dict(canceled)

    def cancel_subscription_at_period_end(self, subscription_id: str) -> dict:
        """
        Schedules a subscription to cancel at the end of the current billing
        period rather than immediately.

        The status remains "active" and the user retains full paid-tier access
        until current_period_end. Stripe then fires customer.subscription.deleted,
        which the webhook processor uses to downgrade the user to Free.

        This is the default cancellation behaviour: the user keeps the access
        they paid for until the period expires.

        Args:
            subscription_id: Stripe Subscription ID (sub_...).

        Returns:
            Updated subscription dict (status="active",
            cancel_at_period_end=True).

        Raises:
            StripeClientError: On Stripe API failure.
        """
        updated = self._call(
            self._client.v1.subscriptions.update,
            subscription_id,
            {"cancel_at_period_end": True},
        )
        return self._to_dict(updated)

    def reactivate_subscription(self, subscription_id: str) -> dict:
        """
        Reverses a scheduled end-of-period cancellation.

        Only valid when status == "active" and cancel_at_period_end == True.
        Sets cancel_at_period_end=False, restoring normal renewal behaviour.
        The user's tier is unaffected (it was never changed by the schedule).

        Args:
            subscription_id: Stripe Subscription ID (sub_...).

        Returns:
            Updated subscription dict (cancel_at_period_end=False).

        Raises:
            StripeClientError: On Stripe API failure.
        """
        updated = self._call(
            self._client.v1.subscriptions.update,
            subscription_id,
            {"cancel_at_period_end": False},
        )
        return self._to_dict(updated)

    # ── Webhook verification ──────────────────────────────────────────────────

    def construct_webhook_event(
        self, body: bytes, sig_header: str
    ) -> stripe.Event:
        """
        Verifies a Stripe webhook signature and constructs the Event object.

        CRITICAL — raw bytes required:
            This method MUST be called with the exact bytes Stripe sent,
            before any JSON parsing. In FastAPI the endpoint must use:
                body = await request.body()
            and pass those bytes directly. A pre-parsed dict will cause
            signature verification to fail.

        The module-level stripe.Webhook.construct_event is used here
        (not a client instance method) because webhook signature verification
        is independent of the API key — it only requires the webhook secret.

        Args:
            body:       Raw request body bytes from the HTTP request.
            sig_header: Value of the "Stripe-Signature" HTTP header.

        Returns:
            Verified stripe.Event object. Access event.type and
            event.data.object in the webhook processor.

        Raises:
            StripeWebhookError: If the webhook_secret is not configured,
                                the signature is invalid, the timestamp
                                is outside the tolerance window (5 min),
                                or the payload is not valid JSON.
        """
        if not self._webhook_secret:
            raise StripeWebhookError(
                "Stripe webhook secret is not configured. "
                "Set the STRIPE_WEBHOOK_SECRET environment variable or pass "
                "webhook_secret= to StripeClient()."
            )

        try:
            return stripe.Webhook.construct_event(
                payload=body,
                sig_header=sig_header,
                secret=self._webhook_secret,
            )
        except stripe.SignatureVerificationError as exc:
            raise StripeWebhookError(
                f"Webhook signature verification failed: {exc}"
            ) from exc
        except ValueError as exc:
            # Raised by stripe SDK when payload is not valid JSON.
            raise StripeWebhookError(
                f"Webhook payload is not valid JSON: {exc}"
            ) from exc
