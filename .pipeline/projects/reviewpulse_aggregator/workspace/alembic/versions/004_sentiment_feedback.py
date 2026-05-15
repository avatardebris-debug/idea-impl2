"""add sentiment feedback

Revision ID: 004
Revises: 003
Create Date: 2026-05-13 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # We add sentiment_feedback column
    op.add_column('reviews', sa.Column('sentiment_feedback', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('reviews', 'sentiment_feedback')
