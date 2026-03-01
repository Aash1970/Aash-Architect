from fastapi import APIRouter, Request, Header, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.billing.subscription_service import SubscriptionService
from app.billing.webhook_processor import WebhookProcessor
from app.services.data_service import DataService

router = APIRouter()


def get_data_service() -> DataService:
    return app.state.data_service


@router.post("/create-checkout-session")
async def create_checkout_session(
    user_id: str,
    price_id: str,
    ds: DataService = Depends(get_data_service),
):
    svc = SubscriptionService(ds)
    session = svc.create_checkout_session(user_id, price_id)
    return {"url": session["url"]}


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    ds: DataService = Depends(get_data_service),
):
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    body = await request.body()

    processor = WebhookProcessor(ds)

    try:
        result = processor.process(body, stripe_signature)
        return JSONResponse(content=result)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook")