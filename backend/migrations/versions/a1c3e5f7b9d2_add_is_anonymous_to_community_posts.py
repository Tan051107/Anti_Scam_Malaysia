"""add is_anonymous to community_posts

Revision ID: a1c3e5f7b9d2
Revises: f9a2d8e4ea42
Create Date: 2025-05-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1c3e5f7b9d2'
down_revision = 'f9a2d8e4ea42'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'community_posts',
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('community_posts', 'is_anonymous')
