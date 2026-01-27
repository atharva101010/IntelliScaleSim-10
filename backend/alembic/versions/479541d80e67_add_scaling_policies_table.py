"""add scaling_policies table

Revision ID: 479541d80e67
Revises: 83c62c5555bc
Create Date: 2026-01-14 06:02:34.150234

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '479541d80e67'
down_revision: Union[str, Sequence[str], None] = '83c62c5555bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'scaling_policies',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('container_id', sa.Integer(), sa.ForeignKey('containers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        
        # Scale Up Configuration
        sa.Column('scale_up_cpu_threshold', sa.Float(), nullable=False, server_default='80.0'),
        sa.Column('scale_up_memory_threshold', sa.Float(), nullable=False, server_default='80.0'),
        sa.Column('min_replicas', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_replicas', sa.Integer(), nullable=False, server_default='8'),
        
        # Scale Down Configuration
        sa.Column('scale_down_cpu_threshold', sa.Float(), nullable=False, server_default='30.0'),
        sa.Column('scale_down_memory_threshold', sa.Float(), nullable=False, server_default='30.0'),
        
        # Load Balancing
        sa.Column('load_balancer_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('load_balancer_port', sa.Integer(), nullable=True),
        
        # Timing
        sa.Column('cooldown_period', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('evaluation_period', sa.Integer(), nullable=False, server_default='60'),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_scaled_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for foreign keys
    op.create_index('ix_scaling_policies_container_id', 'scaling_policies', ['container_id'])
    op.create_index('ix_scaling_policies_user_id', 'scaling_policies', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_scaling_policies_user_id', table_name='scaling_policies')
    op.drop_index('ix_scaling_policies_container_id', table_name='scaling_policies')
    op.drop_table('scaling_policies')
