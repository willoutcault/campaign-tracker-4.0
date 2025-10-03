"""0003_program_plat_asset

Revision ID: 0003_program_plat_asset
Revises: 0002_m2m_placements
Create Date: 2025-10-03 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_program_plat_asset'
down_revision = '0002_m2m_placements'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('program', sa.Column('platform', sa.String(length=255), nullable=True))
    op.add_column('program', sa.Column('asset_id', sa.String(length=255), nullable=True))

def downgrade():
    op.drop_column('program', 'asset_id')
    op.drop_column('program', 'platform')
