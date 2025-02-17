"""Add metadata column to code_patterns

Revision ID: 002
Revises: 001
Create Date: 2025-02-12 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Skip adding metadata column since it's already in initial migration
    pass

def downgrade() -> None:
    # Skip removing metadata column since it's managed by initial migration
    pass