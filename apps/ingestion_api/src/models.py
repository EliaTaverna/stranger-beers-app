"""SQLAlchemy async models for the Ingestion API."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class Registration(Base):
    """
    A registration for a Stranger Beers event.

    Created/updated by signup form webhook.
    Marked as paid by payment form webhook.
    """

    __tablename__ = "registrations"

    # Primary key - text-based registration ID from Tally hidden field
    registration_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Event identification
    event_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Contact info
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_e164: Mapped[str | None] = mapped_column(String(50), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Signup data
    signup_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    signup_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Payment status
    paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payment_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    payment_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Payment linkage info - what the payment form claimed
    payment_claimed_registration_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    payment_claimed_phone_e164: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    # How the payment was linked
    # Values: 'unpaid', 'matched_by_registration_id', 'matched_by_phone',
    #         'orphan_payment', 'ambiguous_phone_match'
    payment_link_status: Mapped[str] = mapped_column(
        String(50), default="unpaid", nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Indexes
    __table_args__ = (
        Index("ix_registrations_event_phone", "event_id", "phone_e164"),
    )

    def __repr__(self) -> str:
        return f"<Registration(registration_id={self.registration_id!r}, event_id={self.event_id!r}, paid={self.paid})>"


class Signup(Base):
    """Record of signup form submissions."""

    __tablename__ = "signups"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    first_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    age: Mapped[str | None] = mapped_column(String(10), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    background: Mapped[str | None] = mapped_column(Text, nullable=True)
    creative_expression_score: Mapped[int | None] = mapped_column(nullable=True)
    social_anxiety_score: Mapped[int | None] = mapped_column(nullable=True)
    emotional_intuition_score: Mapped[int | None] = mapped_column(nullable=True)
    solitary_preference_score: Mapped[int | None] = mapped_column(nullable=True)
    interests_active_outdoors: Mapped[str | None] = mapped_column(Text, nullable=True)
    interests_creativity: Mapped[str | None] = mapped_column(Text, nullable=True)
    interests_intellectual: Mapped[str | None] = mapped_column(Text, nullable=True)
    interests_food_social: Mapped[str | None] = mapped_column(Text, nullable=True)
    interests_games: Mapped[str | None] = mapped_column(Text, nullable=True)
    interests_mind_self: Mapped[str | None] = mapped_column(Text, nullable=True)
    mbti: Mapped[str | None] = mapped_column(String(50), nullable=True)
    optional_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Signup(id={self.id}, first_name={self.first_name!r})>"


class Payment(Base):
    """Record of payment form submissions."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    arrived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str | None] = mapped_column(Text, nullable=True)
    recognized: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, phone={self.phone!r}, recognized={self.recognized})>"
