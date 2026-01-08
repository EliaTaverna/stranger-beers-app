"""Common Pydantic types for Stranger Beers services."""

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from shared.phone import normalize_phone


# Type aliases for documentation
UserId = UUID
MatchId = UUID
RegistrationId = UUID


class PhoneNumber(str):
    """
    A validated and normalized phone number in E.164 format.

    Use as a Pydantic field type for automatic validation and normalization.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema

        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
        )

    @classmethod
    def _validate(cls, v: str) -> "PhoneNumber":
        normalized = normalize_phone(v)
        if normalized is None:
            raise ValueError(f"Invalid phone number: {v}")
        return cls(normalized)


# Annotated types for common fields
Email = Annotated[EmailStr, Field(description="Valid email address")]


class BaseEntity(BaseModel):
    """Base model for all database entities."""

    class Config:
        from_attributes = True
        populate_by_name = True


class Registration(BaseEntity):
    """A user registration for a Stranger Beers event."""

    id: RegistrationId | None = None
    name: str = Field(..., min_length=1, max_length=100)
    email: Email
    phone: PhoneNumber
    city: str = Field(..., min_length=1, max_length=100)


class Match(BaseEntity):
    """A match between two registrations."""

    id: MatchId | None = None
    registration_a_id: RegistrationId
    registration_b_id: RegistrationId
    round_number: int = Field(..., ge=1)
