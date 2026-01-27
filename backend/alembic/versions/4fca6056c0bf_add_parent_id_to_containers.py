"""add parent_id to containers

Revision ID: 4fca6056c0bf
Revises: 355769e843e1
Create Date: 2026-01-14 06:07:40.418382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fca6056c0bf'
down_revision: Union[str, Sequence[str], None] = '355769e843e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('containers', sa.Column('parent_id', sa.Integer(), sa.ForeignKey('containers.id'), nullable=True))
    op.create_index('ix_containers_parent_id', 'containers', ['parent_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_containers_parent_id', table_name='containers')
    op.drop_column('containers', 'parent_id')
