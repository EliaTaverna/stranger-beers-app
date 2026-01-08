"""Stranger Beers shared utilities package."""

from shared.logging import configure_logging
from shared.phone import normalize_phone
from shared.types import PhoneNumber, Email, UserId

__version__ = "0.1.0"

__all__ = [
    "configure_logging",
    "normalize_phone",
    "PhoneNumber",
    "Email",
    "UserId",
]
