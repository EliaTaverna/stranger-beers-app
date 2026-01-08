"""Payment form processing service."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Registration, Payment, Signup
from ..tally.parse import ParsedPaymentData

logger = logging.getLogger("stranger-beers.services.payment")


class PaymentLinkStatus(str, Enum):
    """Payment link status values."""

    MATCHED_BY_REGISTRATION_ID = "matched_by_registration_id"
    MATCHED_BY_PHONE = "matched_by_phone"
    ORPHAN_PAYMENT = "orphan_payment"
    AMBIGUOUS_PHONE_MATCH = "ambiguous_phone_match"


@dataclass
class PaymentResult:
    """Result of processing a payment form submission."""

    success: bool
    registration_id: str | None
    link_status: PaymentLinkStatus | None
    is_emergency: bool
    error_message: str | None = None


async def process_payment(
    session: AsyncSession,
    parsed: ParsedPaymentData,
    body_hash: str,
) -> PaymentResult:
    """
    Process a payment form submission.

    Matching logic:
    1. Try to match by registration_id
       - If found: mark as paid with status 'matched_by_registration_id'
    2. If no match, try to match by (event_id + phone_e164)
       - If exactly one match: mark as paid with status 'matched_by_phone'
       - If zero matches: EMERGENCY - flag as 'orphan_payment'
       - If multiple matches: EMERGENCY - flag as 'ambiguous_phone_match'

    Args:
        session: Database session
        parsed: Parsed payment form data
        body_hash: SHA-256 hash of the raw request body

    Returns:
        PaymentResult with processing outcome
    """
    # Log incoming data for debugging
    print(f"Payment parsed data: registration_id={parsed.registration_id}, phone={parsed.phone_e164}, event_id={parsed.event_id}")
    print(f"Raw payload fields: {[f.get('label') for f in parsed.raw_payload.get('data', {}).get('fields', [])]}")

    # Validate we have at least one identifier to match on
    if not parsed.registration_id and not parsed.phone_e164:
        error_msg = "Payment has neither registration_id nor valid phone number"
        logger.error(error_msg)
        return PaymentResult(
            success=False,
            registration_id=None,
            link_status=None,
            is_emergency=True,
            error_message=error_msg,
        )

    now = datetime.now(timezone.utc)

    # Step 1: Try to match by registration_id
    if parsed.registration_id:
        registration = await session.get(Registration, parsed.registration_id)
        if registration:
            # Found by registration_id
            await _mark_paid(
                registration,
                parsed,
                now,
                PaymentLinkStatus.MATCHED_BY_REGISTRATION_ID,
            )
            # Log the submission
            await _log_submission(session, parsed)
            logger.info(
                f"Payment matched by registration_id: {parsed.registration_id}"
            )
            return PaymentResult(
                success=True,
                registration_id=registration.registration_id,
                link_status=PaymentLinkStatus.MATCHED_BY_REGISTRATION_ID,
                is_emergency=False,
            )

    # Step 2: Try to match by (event_id + phone_e164)
    if parsed.event_id and parsed.phone_e164:
        matches = await _find_by_event_and_phone(
            session, parsed.event_id, parsed.phone_e164
        )

        if len(matches) == 1:
            # Exactly one match by phone
            registration = matches[0]
            await _mark_paid(
                registration,
                parsed,
                now,
                PaymentLinkStatus.MATCHED_BY_PHONE,
            )
            # Log the submission
            await _log_submission(session, parsed)
            logger.info(
                f"Payment matched by phone: {parsed.phone_e164} -> "
                f"registration {registration.registration_id}"
            )
            return PaymentResult(
                success=True,
                registration_id=registration.registration_id,
                link_status=PaymentLinkStatus.MATCHED_BY_PHONE,
                is_emergency=False,
            )

        elif len(matches) > 1:
            # EMERGENCY: Multiple matches - ambiguous phone (but still recognized)
            await _log_submission(session, parsed)
            logger.error(
                f"EMERGENCY: Ambiguous phone match! phone={parsed.phone_e164}, "
                f"event_id={parsed.event_id}, matches={[r.registration_id for r in matches]}"
            )
            return PaymentResult(
                success=True,  # We processed it, but it's an emergency
                registration_id=None,
                link_status=PaymentLinkStatus.AMBIGUOUS_PHONE_MATCH,
                is_emergency=True,
                error_message=f"Multiple registrations found for phone {parsed.phone_e164}",
            )

    # EMERGENCY: No matches found - orphan payment (not recognized)
    await _log_submission(session, parsed)
    logger.error(
        f"EMERGENCY: Orphan payment! registration_id={parsed.registration_id}, "
        f"phone={parsed.phone_e164}, event_id={parsed.event_id}"
    )
    return PaymentResult(
        success=True,  # We processed it, but it's an emergency
        registration_id=None,
        link_status=PaymentLinkStatus.ORPHAN_PAYMENT,
        is_emergency=True,
        error_message="No matching registration found for payment",
    )


async def _mark_paid(
    registration: Registration,
    parsed: ParsedPaymentData,
    now: datetime,
    status: PaymentLinkStatus,
) -> None:
    """Mark a registration as paid."""
    registration.paid = True
    registration.paid_at = now
    registration.payment_payload = parsed.raw_payload
    registration.payment_received_at = now
    registration.payment_claimed_registration_id = parsed.registration_id
    registration.payment_claimed_phone_e164 = parsed.phone_e164
    registration.payment_link_status = status.value
    registration.updated_at = now


async def _find_by_event_and_phone(
    session: AsyncSession,
    event_id: str,
    phone_e164: str,
) -> list[Registration]:
    """Find all registrations matching event_id and phone_e164."""
    stmt = select(Registration).where(
        and_(
            Registration.event_id == event_id,
            Registration.phone_e164 == phone_e164,
        )
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _check_phone_in_signups(session: AsyncSession, phone: str) -> bool:
    """Check if a phone number exists in the signups table."""
    stmt = select(Signup).where(Signup.phone == phone).limit(1)
    result = await session.execute(stmt)
    return result.scalar() is not None


async def _log_submission(
    session: AsyncSession,
    parsed: ParsedPaymentData,
) -> Payment:
    """Log a submission to the payments table."""
    phone = parsed.phone_e164 or parsed.phone_raw

    # Check if phone exists in signups table
    recognized = False
    if phone:
        recognized = await _check_phone_in_signups(session, phone)

    # Extract status from "All done?" field
    status = None
    for field in parsed.raw_payload.get("data", {}).get("fields", []):
        if "All done" in field.get("label", ""):
            value = field.get("value")
            if isinstance(value, list) and field.get("options"):
                # Resolve option IDs to text
                option_lookup = {opt.get("id"): opt.get("text") for opt in field.get("options", [])}
                status = ", ".join(option_lookup.get(v, str(v)) for v in value)
            else:
                status = str(value) if value else None
            break

    submission = Payment(
        phone=phone,
        status=status,
        recognized=recognized,
    )
    session.add(submission)
    return submission
