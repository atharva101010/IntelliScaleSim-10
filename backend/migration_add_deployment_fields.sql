"""Add real deployment fields to containers

Revision ID: add_deployment_fields
Revises: 
Create Date: 2025-12-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_deployment_fields'
down_revision = None

def upgrade():
    # Add new columns for real deployments
    op.add_column('containers', sa.Column('deployment_type', sa.String(20), nullable=True))
    op.add_column('containers', sa.Column('source_url', sa.Text(), nullable=True))
    op.add_column('containers', sa.Column('build_status', sa.String(20), nullable=True))
    op.add_column('containers', sa.Column('build_logs', sa.Text(), nullable=True))
    op.add_column('containers', sa.Column('container_id', sa.String(255), nullable=True))
    op.add_column('containers', sa.Column('localhost_url', sa.String(500), nullable=True))
    op.add_column('containers', sa.Column('public_url', sa.String(500), nullable=True))

def downgrade():
    op.drop_column('containers', 'public_url')
    op.drop_column('containers', 'localhost_url')
    op.drop_column('containers', 'container_id')
    op.drop_column('containers', 'build_logs')
    op.drop_column('containers', 'build_status')
    op.drop_column('containers', 'source_url')
    op.drop_column('containers', 'deployment_type')
