"""Initial tables for registrations and tally_submissions.

Revision ID: 0001
Revises:
Create Date: 2024-12-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create registrations table
    op.create_table(
        "registrations",
        sa.Column("registration_id", sa.String(255), primary_key=True),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone_e164", sa.String(50), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("signup_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("signup_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("payment_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_claimed_registration_id", sa.String(255), nullable=True),
        sa.Column("payment_claimed_phone_e164", sa.String(50), nullable=True),
        sa.Column(
            "payment_link_status",
            sa.String(50),
            nullable=False,
            server_default="unpaid",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create indexes on registrations
    op.create_index("ix_registrations_event_id", "registrations", ["event_id"])
    op.create_index(
        "ix_registrations_event_phone", "registrations", ["event_id", "phone_e164"]
    )

    # Create tally_submissions table (audit log)
    op.create_table(
        "tally_submissions",
        sa.Column(
            "id", sa.BigInteger(), primary_key=True, autoincrement=True
        ),
        sa.Column("form_type", sa.String(50), nullable=False),
        sa.Column("form_id", sa.String(255), nullable=False),
        sa.Column("submission_id", sa.String(255), nullable=True),
        sa.Column("body_hash", sa.String(64), nullable=True),
        sa.Column("event_id", sa.String(255), nullable=True),
        sa.Column("registration_id_claimed", sa.String(255), nullable=True),
        sa.Column("phone_e164_claimed", sa.String(50), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("processed_ok", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("linked_registration_id", sa.String(255), nullable=True),
        sa.Column("link_status", sa.String(50), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create unique constraint for form_id + submission_id (when submission_id is not null)
    # PostgreSQL partial unique index for idempotency
    op.create_index(
        "uq_tally_submissions_form_submission",
        "tally_submissions",
        ["form_id", "submission_id"],
        unique=True,
        postgresql_where=sa.text("submission_id IS NOT NULL"),
    )

    # Create index for body_hash lookups (fallback idempotency)
    op.create_index(
        "ix_tally_submissions_form_body_hash",
        "tally_submissions",
        ["form_id", "body_hash"],
    )


def downgrade() -> None:
    # Drop tally_submissions table
    op.drop_index("ix_tally_submissions_form_body_hash", table_name="tally_submissions")
    op.drop_index("uq_tally_submissions_form_submission", table_name="tally_submissions")
    op.drop_table("tally_submissions")

    # Drop registrations table
    op.drop_index("ix_registrations_event_phone", table_name="registrations")
    op.drop_index("ix_registrations_event_id", table_name="registrations")
    op.drop_table("registrations")
