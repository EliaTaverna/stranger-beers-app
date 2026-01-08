"""FastAPI application for receiving Tally form submissions."""

import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db import close_db, get_session, init_db
from .services.payment import PaymentLinkStatus, process_payment
from .services.signup import process_signup
from shared import configure_logging
from .tally.parse import (
    ParsedPaymentData,
    ParsedSignupData,
    compute_body_hash,
    determine_form_type,
    parse_tally_payload,
)
from .tally.verify import verify_tally_signature

# Configure logging
logger = configure_logging(settings.log_level, "ingestion-api", settings.log_json)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting Ingestion API")
    await init_db()
    logger.info("Database initialized")
    yield
    await close_db()
    logger.info("Shutting down Ingestion API")


app = FastAPI(
    title="Stranger Beers Ingestion API",
    description="Webhook receiver for Tally form submissions",
    version="0.1.0",
    lifespan=lifespan,
)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str


class WebhookResponse(BaseModel):
    """Response from webhook endpoints."""

    status: str
    form_type: str | None = None
    registration_id: str | None = None
    link_status: str | None = None
    is_emergency: bool = False
    message: str | None = None


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", service="ingestion-api")


@app.post("/webhooks/tally", status_code=status.HTTP_201_CREATED)
async def receive_tally_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> WebhookResponse:
    """
    Receive and process Tally form submissions.

    This endpoint receives webhook payloads from Tally for both
    signup and payment forms. The form type is determined by the form_id.
    """
    # Read raw body first (for hashing and signature verification)
    body = await request.body()
    body_hash = compute_body_hash(body)

    # Parse JSON
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Extract form_id to determine form type
    data = payload.get("data", {})
    form_id = data.get("formId", "")

    if not form_id:
        logger.error("Missing formId in payload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing formId in payload",
        )

    # Determine form type
    form_type = determine_form_type(form_id)
    if form_type is None:
        logger.warning(f"Unknown form_id: {form_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown form_id: {form_id}",
        )

    logger.info(f"Received {form_type} webhook: form_id={form_id}")

    # Verify signature if enabled
    signature_header = request.headers.get("tally-signature")
    is_valid, error = verify_tally_signature(body, signature_header, form_type)
    if not is_valid:
        logger.error(f"Signature verification failed: {error}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
        )

    # Parse the payload
    parsed = parse_tally_payload(payload, form_type)

    # Route to appropriate handler
    if form_type == "signup":
        return await _handle_signup(session, parsed, body_hash)
    else:
        return await _handle_payment(session, parsed, body_hash)


async def _handle_signup(
    session: AsyncSession,
    parsed: ParsedSignupData,
    body_hash: str,
) -> WebhookResponse:
    """Handle a signup form submission."""
    result = await process_signup(session, parsed, body_hash)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error_message or "Failed to process signup",
        )

    return WebhookResponse(
        status="received",
        form_type="signup",
        registration_id=result.registration_id,
        message="created" if result.is_new else "updated",
    )


async def _handle_payment(
    session: AsyncSession,
    parsed: ParsedPaymentData,
    body_hash: str,
) -> WebhookResponse:
    """Handle a payment form submission."""
    result = await process_payment(session, parsed, body_hash)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error_message or "Failed to process payment",
        )

    return WebhookResponse(
        status="received",
        form_type="payment",
        registration_id=result.registration_id,
        link_status=result.link_status.value if result.link_status else None,
        is_emergency=result.is_emergency,
        message=result.error_message if result.is_emergency else "paid",
    )


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "service": "Stranger Beers Ingestion API",
        "version": "0.1.0",
        "docs": "/docs",
    }
