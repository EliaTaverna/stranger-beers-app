"""Tally webhook payload parsing utilities."""

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from shared import normalize_phone

from ..config import settings


# ============================================================================
# Field Mapping Layer
# ============================================================================
# Each form has a mapping from logical field names to Tally field keys.
# This allows changing Tally forms without modifying business logic.
# Keys are looked up in the order: field key (question_xxx), then label fallback.
# ============================================================================

# Signup form field mapping
SIGNUP_FIELD_MAP = {
    # Hidden fields (set by URL parameters)
    "registration_id": ["registration_id", "registrationId", "Registration ID"],
    "event_id": ["event_id", "eventId", "Event ID"],
    # User-provided fields
    "phone": ["phone", "Phone", "phone_number", "Phone Number", "Mobile"],
    "email": ["email", "Email", "email_address", "Email Address"],
    "full_name": ["full_name", "name", "Name", "Full Name", "Your Name"],
}

# Form field mapping for extracting all Tally form fields
FORM_FIELD_MAP = {
    "first_name": ["question_EQROMA", "What's your first name?"],
    "phone": ["question_rA4Zvp", "Whats your phone number?"],
    "first_time": ["question_4x6bzd", "First time at Stranger Beers?"],
    "age": ["question_72AkM6", "How old are you?"],
    "gender": ["question_jQRVvY", "How do you identify?"],
    "country": ["question_62lBMo", "Where are you from"],
    "background": ["question_ALgXyo", "What's your background"],
    "creative_expression_score": ["question_2NW67g", "creative expression"],
    "social_anxiety_score": ["question_xaqWvE", "feel nervous"],
    "emotional_intuition_score": ["question_NWjZdN", "emotional intuition"],
    "solitary_preference_score": ["question_Z67BDA", "solitary hobbies"],
    "interests_active_outdoors": ["question_qArlv8", "Active & Outdoors"],
    "interests_creativity": ["question_Q5ZQkl", "Creativity & Expression"],
    "interests_intellectual": ["question_9DkKMK", "Intellectual & Curious"],
    "interests_food_social": ["question_eeJXvJ", "Food & Social"],
    "interests_games": ["question_W5W71L", "Games & Collecting"],
    "interests_mind_self": ["question_aYLMvW", "Mind & Self"],
    "mbti": ["question_bxpJv0", "MBTI"],
    "optional_note": ["question_BkyRe4", "One last"],
}

# Payment form field mapping
PAYMENT_FIELD_MAP = {
    # Hidden fields
    "registration_id": ["registration_id", "registrationId", "Registration ID"],
    "event_id": ["event_id", "eventId", "Event ID"],
    # User-provided fields
    "phone": ["phone", "Phone", "phone_number", "Phone Number", "Mobile", "What's the phone number you signed up with?"],
    "email": ["email", "Email", "email_address", "Email Address", "Reserve your drink! (email)"],
}


@dataclass
class ExtractedFormFields:
    """Extracted form field values from a Tally submission."""

    first_name: str | None = None
    phone: str | None = None
    first_time: str | None = None
    age: str | None = None
    gender: str | None = None
    country: str | None = None
    background: str | None = None
    creative_expression_score: int | None = None
    social_anxiety_score: int | None = None
    emotional_intuition_score: int | None = None
    solitary_preference_score: int | None = None
    interests_active_outdoors: str | None = None
    interests_creativity: str | None = None
    interests_intellectual: str | None = None
    interests_food_social: str | None = None
    interests_games: str | None = None
    interests_mind_self: str | None = None
    mbti: str | None = None
    optional_note: str | None = None


@dataclass
class ParsedSignupData:
    """Parsed data from a signup form submission."""

    form_id: str
    submission_id: str | None
    event_id: str | None
    registration_id: str | None
    phone_raw: str | None
    phone_e164: str | None
    email: str | None
    full_name: str | None
    raw_payload: dict[str, Any]
    form_fields: ExtractedFormFields | None = None


@dataclass
class ParsedPaymentData:
    """Parsed data from a payment form submission."""

    form_id: str
    submission_id: str | None
    event_id: str | None
    registration_id: str | None
    phone_raw: str | None
    phone_e164: str | None
    email: str | None
    raw_payload: dict[str, Any]


def compute_body_hash(body: bytes) -> str:
    """Compute SHA-256 hash of the raw request body."""
    return hashlib.sha256(body).hexdigest()


def extract_field_value(
    fields: list[dict[str, Any]],
    logical_name: str,
    field_map: dict[str, list[str]],
) -> str | None:
    """
    Extract a field value from Tally fields using the mapping layer.

    Args:
        fields: List of Tally field objects with 'key', 'label', 'value'
        logical_name: The logical field name (e.g., 'phone', 'email')
        field_map: Mapping from logical names to possible Tally keys/labels

    Returns:
        The field value as a string, or None if not found
    """
    possible_keys = field_map.get(logical_name, [])
    if not possible_keys:
        return None

    # Build lookup dicts for fast access
    by_key: dict[str, Any] = {}
    by_label: dict[str, Any] = {}

    for field in fields:
        key = field.get("key", "")
        label = field.get("label", "")
        value = field.get("value")

        if key:
            by_key[key.lower()] = value
        if label:
            by_label[label.lower()] = value

    # Search in order of preference
    for candidate in possible_keys:
        candidate_lower = candidate.lower()
        # Try by key first
        if candidate_lower in by_key:
            value = by_key[candidate_lower]
            return _normalize_value(value)
        # Then by label
        if candidate_lower in by_label:
            value = by_label[candidate_lower]
            return _normalize_value(value)

    return None


def _normalize_value(value: Any) -> str | None:
    """Normalize a field value to a string."""
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    if isinstance(value, list):
        # Join multiple values (e.g., multi-select)
        non_empty = [str(v).strip() for v in value if v]
        return ", ".join(non_empty) if non_empty else None
    return str(value).strip() or None


def _resolve_option_text(field: dict[str, Any]) -> str | None:
    """Resolve option IDs to their text values for choice fields."""
    value = field.get("value")
    options = field.get("options", [])

    if not value or not options:
        return _normalize_value(value)

    # Build option lookup
    option_lookup = {opt.get("id"): opt.get("text") for opt in options}

    if isinstance(value, list):
        # Multi-select: resolve each ID to text
        texts = []
        for v in value:
            if v in option_lookup:
                texts.append(option_lookup[v])
            else:
                texts.append(str(v))
        return ", ".join(texts) if texts else None
    elif value in option_lookup:
        return option_lookup[value]

    return _normalize_value(value)


def extract_form_fields(fields: list[dict[str, Any]]) -> ExtractedFormFields:
    """Extract all form field values from Tally fields."""
    result = ExtractedFormFields()

    # Build lookup by key
    fields_by_key = {f.get("key", "").lower(): f for f in fields}

    for attr_name, possible_keys in FORM_FIELD_MAP.items():
        for key in possible_keys:
            key_lower = key.lower()
            if key_lower in fields_by_key:
                field = fields_by_key[key_lower]
                field_type = field.get("type", "")

                # Handle different field types
                if field_type in ("MULTIPLE_CHOICE", "DROPDOWN", "MULTI_SELECT"):
                    value = _resolve_option_text(field)
                elif field_type == "LINEAR_SCALE":
                    raw_value = field.get("value")
                    value = int(raw_value) if raw_value is not None else None
                else:
                    value = _normalize_value(field.get("value"))

                # Set the attribute based on type
                if attr_name.endswith("_score"):
                    setattr(result, attr_name, value if isinstance(value, int) else None)
                else:
                    setattr(result, attr_name, value if isinstance(value, str) else str(value) if value else None)
                break

    return result


def parse_tally_payload(
    payload: dict[str, Any],
    form_type: str,
) -> ParsedSignupData | ParsedPaymentData:
    """
    Parse a Tally webhook payload into structured data.

    Args:
        payload: The parsed JSON payload from Tally
        form_type: Either 'signup' or 'payment'

    Returns:
        ParsedSignupData or ParsedPaymentData depending on form_type
    """
    # Extract top-level fields
    data = payload.get("data", {})
    form_id = data.get("formId", "")
    submission_id = data.get("submissionId") or data.get("responseId")

    # Get fields array
    fields = data.get("fields", [])

    # Select the appropriate field map
    field_map = SIGNUP_FIELD_MAP if form_type == "signup" else PAYMENT_FIELD_MAP

    # Extract common fields
    event_id = extract_field_value(fields, "event_id", field_map)
    registration_id = extract_field_value(fields, "registration_id", field_map)
    phone_raw = extract_field_value(fields, "phone", field_map)
    email = extract_field_value(fields, "email", field_map)

    # Normalize phone to E.164
    phone_e164 = None
    if phone_raw:
        phone_e164 = normalize_phone(phone_raw, settings.default_phone_region)

    if form_type == "signup":
        full_name = extract_field_value(fields, "full_name", field_map)
        # Extract all form fields for signup forms
        form_fields = extract_form_fields(fields)
        return ParsedSignupData(
            form_id=form_id,
            submission_id=submission_id,
            event_id=event_id,
            registration_id=registration_id,
            phone_raw=phone_raw,
            phone_e164=phone_e164,
            email=email,
            full_name=full_name,
            raw_payload=payload,
            form_fields=form_fields,
        )
    else:
        return ParsedPaymentData(
            form_id=form_id,
            submission_id=submission_id,
            event_id=event_id,
            registration_id=registration_id,
            phone_raw=phone_raw,
            phone_e164=phone_e164,
            email=email,
            raw_payload=payload,
        )


def determine_form_type(form_id: str) -> str | None:
    """
    Determine if a form_id corresponds to signup or payment form.

    Returns:
        'signup', 'payment', or None if unknown
    """
    if form_id == settings.tally_signup_form_id:
        return "signup"
    if form_id == settings.tally_payment_form_id:
        return "payment"
    return None
