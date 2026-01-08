"""Tally webhook signature verification."""

import hmac
import hashlib
from typing import Tuple

from ..config import settings


class SignatureVerificationError(Exception):
    """Raised when webhook signature verification fails."""

    pass


def verify_tally_signature(
    body: bytes,
    signature_header: str | None,
    form_type: str,
) -> Tuple[bool, str | None]:
    """
    Verify the Tally webhook signature.

    Tally uses HMAC-SHA256 to sign webhook payloads. The signature is
    sent in the 'tally-signature' header.

    Args:
        body: Raw request body bytes
        signature_header: Value of the 'tally-signature' header
        form_type: Either 'signup' or 'payment' to select the correct secret

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if verification passed or is disabled
        - (False, error_message) if verification failed
    """
    # Check if verification is enabled
    if not settings.verify_tally_signature:
        return True, None

    # Get the appropriate secret
    if form_type == "signup":
        secret = settings.tally_signup_secret
    elif form_type == "payment":
        secret = settings.tally_payment_secret
    else:
        return False, f"Unknown form type: {form_type}"

    # Validate secret is configured
    if not secret:
        return False, f"Signature verification enabled but no secret configured for {form_type} form"

    # Validate signature header is present
    if not signature_header:
        return False, "Missing tally-signature header"

    # Compute expected signature
    expected_signature = compute_hmac_sha256(body, secret)

    # Compare signatures using constant-time comparison
    if not hmac.compare_digest(signature_header, expected_signature):
        return False, "Invalid signature"

    return True, None


def compute_hmac_sha256(body: bytes, secret: str) -> str:
    """
    Compute HMAC-SHA256 signature for the given body and secret.

    Args:
        body: Raw request body bytes
        secret: The webhook signing secret

    Returns:
        Hex-encoded HMAC-SHA256 signature
    """
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()
