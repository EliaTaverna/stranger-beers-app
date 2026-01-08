"""Simplify tally_submissions table - keep only id, received_at, and form fields.

Revision ID: 0003
Revises: 0002
Create Date: 2026-01-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop indexes if they exist (use execute to handle case where they don't exist)
    op.execute("DROP INDEX IF EXISTS uq_tally_submissions_form_submission")
    op.execute("DROP INDEX IF EXISTS ix_tally_submissions_form_body_hash")

    # Drop unused columns
    op.drop_column("tally_submissions", "form_type")
    op.drop_column("tally_submissions", "form_id")
    op.drop_column("tally_submissions", "submission_id")
    op.drop_column("tally_submissions", "body_hash")
    op.drop_column("tally_submissions", "event_id")
    op.drop_column("tally_submissions", "registration_id_claimed")
    op.drop_column("tally_submissions", "phone_e164_claimed")
    op.drop_column("tally_submissions", "payload")
    op.drop_column("tally_submissions", "processed_ok")
    op.drop_column("tally_submissions", "error_message")
    op.drop_column("tally_submissions", "linked_registration_id")
    op.drop_column("tally_submissions", "link_status")


def downgrade() -> None:
    # Re-add columns
    op.add_column("tally_submissions", sa.Column("link_status", sa.String(50), nullable=True))
    op.add_column("tally_submissions", sa.Column("linked_registration_id", sa.String(255), nullable=True))
    op.add_column("tally_submissions", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("tally_submissions", sa.Column("processed_ok", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("tally_submissions", sa.Column("payload", postgresql.JSONB(), nullable=True))
    op.add_column("tally_submissions", sa.Column("phone_e164_claimed", sa.String(50), nullable=True))
    op.add_column("tally_submissions", sa.Column("registration_id_claimed", sa.String(255), nullable=True))
    op.add_column("tally_submissions", sa.Column("event_id", sa.String(255), nullable=True))
    op.add_column("tally_submissions", sa.Column("body_hash", sa.String(64), nullable=True))
    op.add_column("tally_submissions", sa.Column("submission_id", sa.String(255), nullable=True))
    op.add_column("tally_submissions", sa.Column("form_id", sa.String(255), nullable=False))
    op.add_column("tally_submissions", sa.Column("form_type", sa.String(50), nullable=False))

    # Re-create indexes
    op.create_index("ix_tally_submissions_form_body_hash", "tally_submissions", ["form_id", "body_hash"])
    op.create_index(
        "uq_tally_submissions_form_submission",
        "tally_submissions",
        ["form_id", "submission_id"],
        unique=True,
        postgresql_where=sa.text("submission_id IS NOT NULL"),
    )
