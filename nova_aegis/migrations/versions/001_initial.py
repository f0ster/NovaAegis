"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-02-12 13:10:22.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Code patterns table
    op.create_table(
        'code_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('language', sa.String()),
        sa.Column('framework', sa.String()),
        sa.Column('template', sa.Text(), nullable=False),
        sa.Column('metadata', JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Pattern relations table
    op.create_table(
        'code_pattern_relations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('code_patterns.id'), nullable=False),
        sa.Column('target_id', sa.Integer(), sa.ForeignKey('code_patterns.id'), nullable=False),
        sa.Column('relation_type', sa.String(), nullable=False),
        sa.Column('weight', sa.Float(), default=1.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Pattern usages table
    op.create_table(
        'pattern_usages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pattern_id', sa.Integer(), sa.ForeignKey('code_patterns.id'), nullable=False),
        sa.Column('context', JSON),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Pattern tags association table
    op.create_table(
        'pattern_tags',
        sa.Column('pattern_id', sa.Integer(), sa.ForeignKey('code_patterns.id')),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id')),
        sa.PrimaryKeyConstraint('pattern_id', 'tag_id')
    )

def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('pattern_tags')
    op.drop_table('pattern_usages')
    op.drop_table('code_pattern_relations')
    op.drop_table('code_patterns')
    op.drop_table('tags')