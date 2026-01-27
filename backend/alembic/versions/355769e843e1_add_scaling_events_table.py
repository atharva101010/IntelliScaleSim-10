"""add scaling_events table

Revision ID: 355769e843e1
Revises: 479541d80e67
Create Date: 2026-01-14 06:04:23.134071

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '355769e843e1'
down_revision: Union[str, Sequence[str], None] = '479541d80e67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'scaling_events',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('policy_id', sa.Integer(), sa.ForeignKey('scaling_policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('container_id', sa.Integer(), sa.ForeignKey('containers.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('action', sa.String(20), nullable=False),  # 'scale_up' or 'scale_down'
        sa.Column('trigger_metric', sa.String(20), nullable=False),  # 'cpu' or 'memory'
        sa.Column('metric_value', sa.Float(), nullable=False),
        
        sa.Column('replica_count_before', sa.Integer(), nullable=False),
        sa.Column('replica_count_after', sa.Integer(), nullable=False),
        
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('ix_scaling_events_policy_id', 'scaling_events', ['policy_id'])
    op.create_index('ix_scaling_events_container_id', 'scaling_events', ['container_id'])
    op.create_index('ix_scaling_events_created_at', 'scaling_events', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_scaling_events_created_at', table_name='scaling_events')
    op.drop_index('ix_scaling_events_container_id', table_name='scaling_events')
    op.drop_index('ix_scaling_events_policy_id', table_name='scaling_events')
    op.drop_table('scaling_events')
