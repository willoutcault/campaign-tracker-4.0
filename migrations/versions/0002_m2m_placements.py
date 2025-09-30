
"""placement_m2m_programs

Revision ID: 0002_m2m_placements
Revises: 0001_baseline
Create Date: 2025-09-29 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_m2m_placements'
down_revision = '0001_baseline'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Create association table if not exists
    if not insp.has_table('program_placement'):
        op.create_table(
            'program_placement',
            sa.Column('program_id', sa.Integer(), nullable=False),
            sa.Column('placement_id', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('program_id', 'placement_id')
        )

    # If placement has program_id, backfill and drop column using batch
    cols = [c['name'] for c in insp.get_columns('placement')]
    if 'program_id' in cols:
        # backfill
        op.execute("""
            INSERT OR IGNORE INTO program_placement (program_id, placement_id)
            SELECT program_id, id FROM placement WHERE program_id IS NOT NULL
        """)
        with op.batch_alter_table('placement', schema=None) as batch_op:
            batch_op.drop_column('program_id')

def downgrade():
    # Cannot reliably restore program_id with data; create nullable if needed
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c['name'] for c in insp.get_columns('placement')]
    if 'program_id' not in cols:
        with op.batch_alter_table('placement', schema=None) as batch_op:
            batch_op.add_column(sa.Column('program_id', sa.Integer(), nullable=True))
