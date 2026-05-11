"""Initial migration — create the reviews table.

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the reviews table."""
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("business_id", sa.String(), nullable=False, index=True),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("text", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("sentiment_label", sa.String(), nullable=True),
        sa.Column("review_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("review_hash"),
    )


def downgrade() -> None:
    """Drop the reviews table."""
    op.drop_table("reviews")
