"""add_appointment_procedures

Revision ID: h7i8j9k0l1m2
Revises: a1b2c3d4e5f6
Create Date: 2026-03-20 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'h7i8j9k0l1m2'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', 'g6h7i8j9k0l1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    # 1. Create appointment_procedures table
    op.create_table(
        'appointment_procedures',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('appointment_id', sa.Uuid(), nullable=False),
        sa.Column('procedure_id', sa.Uuid(), nullable=False),
        sa.Column('custom_price_in_cents', sa.Integer(), nullable=True),
        sa.Column('original_price_in_cents', sa.Integer(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id']),
        sa.ForeignKeyConstraint(['procedure_id'], ['procedures.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_appointment_procedures_appointment_id', 'appointment_procedures', ['appointment_id'])
    op.create_index('ix_appointment_procedures_procedure_id', 'appointment_procedures', ['procedure_id'])

    # 2. Migrate existing data: create one row per existing appointment
    # Use dialect-specific UUID generation (PostgreSQL can't parse SQLite functions even in dead branches)
    if is_sqlite:
        uuid_expr = "lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab', abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))"
    else:
        uuid_expr = "gen_random_uuid()::text"

    bind.execute(sa.text(f"""
        INSERT INTO appointment_procedures (id, appointment_id, procedure_id, original_price_in_cents, custom_price_in_cents, duration_minutes, created_at)
        SELECT
            {uuid_expr},
            a.id,
            a.procedure_id,
            COALESCE(p.price_in_cents, a.price_charged),
            CASE WHEN a.price_charged != COALESCE(p.price_in_cents, a.price_charged) THEN a.price_charged ELSE NULL END,
            COALESCE(p.duration_minutes, a.duration_minutes),
            a.created_at
        FROM appointments a
        LEFT JOIN procedures p ON p.id = a.procedure_id
    """))


def downgrade() -> None:
    op.drop_index('ix_appointment_procedures_procedure_id', table_name='appointment_procedures')
    op.drop_index('ix_appointment_procedures_appointment_id', table_name='appointment_procedures')
    op.drop_table('appointment_procedures')
