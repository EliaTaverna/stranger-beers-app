"""Signup form processing service."""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Registration, Signup
from ..tally.parse import ParsedSignupData

logger = logging.getLogger("stranger-beers.services.signup")


@dataclass
class SignupResult:
    """Result of processing a signup form submission."""

    success: bool
    registration_id: str | None
    is_new: bool
    error_message: str | None = None


async def process_signup(
    session: AsyncSession,
    parsed: ParsedSignupData,
    body_hash: str,
) -> SignupResult:
    """
    Process a signup form submission.

    Creates or updates a registration record. Does NOT mark as paid.

    Args:
        session: Database session
        parsed: Parsed signup form data
        body_hash: SHA-256 hash of the raw request body

    Returns:
        SignupResult with processing outcome
    """
    # Generate registration_id if not provided
    registration_id = parsed.registration_id
    if not registration_id:
        registration_id = f"REG-{uuid.uuid4().hex[:12].upper()}"
        logger.info(f"Generated registration_id: {registration_id}")

    # Generate event_id if not provided
    event_id = parsed.event_id
    if not event_id:
        event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"Generated event_id: {event_id}")

    # Check if registration already exists
    existing_registration = await session.get(Registration, registration_id)
    is_new = existing_registration is None
    now = datetime.now(timezone.utc)

    if existing_registration:
        # Update existing registration
        existing_registration.event_id = event_id
        existing_registration.email = parsed.email
        existing_registration.phone_e164 = parsed.phone_e164
        existing_registration.full_name = parsed.full_name
        existing_registration.signup_payload = parsed.raw_payload
        existing_registration.signup_received_at = now
        existing_registration.updated_at = now
        logger.info(f"Updated registration: {registration_id}")
    else:
        # Create new registration
        registration = Registration(
            registration_id=registration_id,
            event_id=event_id,
            email=parsed.email,
            phone_e164=parsed.phone_e164,
            full_name=parsed.full_name,
            signup_payload=parsed.raw_payload,
            signup_received_at=now,
            paid=False,
            payment_link_status="unpaid",
        )
        session.add(registration)
        logger.info(f"Created registration: {registration_id}")

    # Log to signups table
    await _log_submission(session, parsed)

    return SignupResult(
        success=True,
        registration_id=registration_id,
        is_new=is_new,
    )


async def _log_submission(
    session: AsyncSession,
    parsed: ParsedSignupData,
) -> Signup:
    """Log a submission to the signups table."""
    submission = Signup()

    # Add form fields if available
    if parsed.form_fields:
        ff = parsed.form_fields
        submission.first_name = ff.first_name
        submission.phone = ff.phone
        submission.first_time = ff.first_time
        submission.age = ff.age
        submission.gender = ff.gender
        submission.country = ff.country
        submission.background = ff.background
        submission.creative_expression_score = ff.creative_expression_score
        submission.social_anxiety_score = ff.social_anxiety_score
        submission.emotional_intuition_score = ff.emotional_intuition_score
        submission.solitary_preference_score = ff.solitary_preference_score
        submission.interests_active_outdoors = ff.interests_active_outdoors
        submission.interests_creativity = ff.interests_creativity
        submission.interests_intellectual = ff.interests_intellectual
        submission.interests_food_social = ff.interests_food_social
        submission.interests_games = ff.interests_games
        submission.interests_mind_self = ff.interests_mind_self
        submission.mbti = ff.mbti
        submission.optional_note = ff.optional_note

    session.add(submission)
    return submission
