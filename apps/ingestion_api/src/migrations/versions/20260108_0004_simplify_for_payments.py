"""Simplify tally_submissions for payment tracking only.

Revision ID: 0004
Revises: 0003
Create Date: 2026-01-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop all the signup form field columns
    op.drop_column("tally_submissions", "first_name")
    op.drop_column("tally_submissions", "first_time")
    op.drop_column("tally_submissions", "age")
    op.drop_column("tally_submissions", "gender")
    op.drop_column("tally_submissions", "country")
    op.drop_column("tally_submissions", "background")
    op.drop_column("tally_submissions", "creative_expression_score")
    op.drop_column("tally_submissions", "social_anxiety_score")
    op.drop_column("tally_submissions", "emotional_intuition_score")
    op.drop_column("tally_submissions", "solitary_preference_score")
    op.drop_column("tally_submissions", "interests_active_outdoors")
    op.drop_column("tally_submissions", "interests_creativity")
    op.drop_column("tally_submissions", "interests_intellectual")
    op.drop_column("tally_submissions", "interests_food_social")
    op.drop_column("tally_submissions", "interests_games")
    op.drop_column("tally_submissions", "interests_mind_self")
    op.drop_column("tally_submissions", "mbti")
    op.drop_column("tally_submissions", "optional_note")

    # Rename received_at to arrived_at
    op.alter_column("tally_submissions", "received_at", new_column_name="arrived_at")

    # Add new columns for payment tracking
    op.add_column("tally_submissions", sa.Column("status", sa.Text(), nullable=True))
    op.add_column("tally_submissions", sa.Column("recognized", sa.Boolean(), nullable=True))


def downgrade() -> None:
    # Remove payment columns
    op.drop_column("tally_submissions", "recognized")
    op.drop_column("tally_submissions", "status")

    # Rename arrived_at back to received_at
    op.alter_column("tally_submissions", "arrived_at", new_column_name="received_at")

    # Re-add signup form field columns
    op.add_column("tally_submissions", sa.Column("optional_note", sa.Text(), nullable=True))
    op.add_column("tally_submissions", sa.Column("mbti", sa.String(50), nullable=True))
    op.add_column("tally_submissions", sa.Column("interests_mind_self", sa.Text(), nullable=True))
    op.add_column("tally_submissions", sa.Column("interests_games", sa.Text(), nullable=True))
    op.add_column("tally_submissions", sa.Column("interests_food_social", sa.Text(), nullable=True))
    op.add_column("tally_submissions", sa.Column("interests_intellectual", sa.Text(), nullable=True))
    op.add_column("tally_submissions", sa.Column("interests_creativity", sa.Text(), nullable=True))
    op.add_column("tally_submissions", sa.Column("interests_active_outdoors", sa.Text(), nullable=True))
    op.add_column("tally_submissions", sa.Column("solitary_preference_score", sa.Integer(), nullable=True))
    op.add_column("tally_submissions", sa.Column("emotional_intuition_score", sa.Integer(), nullable=True))
    op.add_column("tally_submissions", sa.Column("social_anxiety_score", sa.Integer(), nullable=True))
    op.add_column("tally_submissions", sa.Column("creative_expression_score", sa.Integer(), nullable=True))
    op.add_column("tally_submissions", sa.Column("background", sa.Text(), nullable=True))
    op.add_column("tally_submissions", sa.Column("country", sa.String(100), nullable=True))
    op.add_column("tally_submissions", sa.Column("gender", sa.String(50), nullable=True))
    op.add_column("tally_submissions", sa.Column("age", sa.String(10), nullable=True))
    op.add_column("tally_submissions", sa.Column("first_time", sa.String(50), nullable=True))
    op.add_column("tally_submissions", sa.Column("first_name", sa.String(255), nullable=True))
