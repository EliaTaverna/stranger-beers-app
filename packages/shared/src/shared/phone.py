"""Phone number normalization utilities."""

import phonenumbers
from phonenumbers import NumberParseException


def normalize_phone(
    phone: str,
    default_region: str = "US",
) -> str | None:
    """
    Normalize a phone number to E.164 format.

    Args:
        phone: Raw phone number string (can include spaces, dashes, etc.)
        default_region: ISO 3166-1 alpha-2 country code for parsing numbers
                       without country code (default: "US")

    Returns:
        E.164 formatted phone number (e.g., "+14155551234") or None if invalid

    Examples:
        >>> normalize_phone("(415) 555-1234")
        '+14155551234'
        >>> normalize_phone("+44 20 7946 0958")
        '+442079460958'
        >>> normalize_phone("invalid")
        None
    """
    if not phone or not phone.strip():
        return None

    try:
        parsed = phonenumbers.parse(phone.strip(), default_region)
        if not phonenumbers.is_valid_number(parsed):
            return None
        return phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        )
    except NumberParseException:
        return None


def is_valid_phone(phone: str, default_region: str = "US") -> bool:
    """Check if a phone number is valid."""
    return normalize_phone(phone, default_region) is not None
