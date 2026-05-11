"""Add business profiles and platform credentials tables.

Revision ID: 002_business_profiles
Revises: 001_initial
Create Date: 2024-01-02
"""

from alembic import op
import sqlalchemy as sa

revision = "002_business_profiles"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create business_profiles and platform_credentials tables."""
    op.create_table(
        "business_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "platform_credentials",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("business_profiles.id"), nullable=False, index=True),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column("api_secret", sa.Text(), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("access_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Drop platform_credentials and business_profiles tables."""
    op.drop_table("platform_credentials")
    op.drop_table("business_profiles")
