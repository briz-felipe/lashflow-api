"""extra_services_and_payment_breakdown

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-03-20 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, Sequence[str], None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # ── extra_services table ───────────────────────────────────────────────────
    if 'extra_services' not in existing_tables:
        op.create_table(
            'extra_services',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('professional_id', sa.Uuid(), nullable=False),
            sa.Column('name', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('default_amount_in_cents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('type', sa.String(20), nullable=False, server_default='add'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['professional_id'], ['users.id']),
        )
        op.create_index('ix_extra_services_professional_id', 'extra_services', ['professional_id'])

    # ── payments: breakdown columns ────────────────────────────────────────────
    existing_columns = {c['name'] for c in inspector.get_columns('payments')}

    if 'subtotal_amount_in_cents' not in existing_columns:
        op.add_column('payments', sa.Column(
            'subtotal_amount_in_cents', sa.Integer(), nullable=False, server_default='0'
        ))
    if 'discount_amount_in_cents' not in existing_columns:
        op.add_column('payments', sa.Column(
            'discount_amount_in_cents', sa.Integer(), nullable=False, server_default='0'
        ))
    if 'fee_amount_in_cents' not in existing_columns:
        op.add_column('payments', sa.Column(
            'fee_amount_in_cents', sa.Integer(), nullable=False, server_default='0'
        ))


def downgrade() -> None:
    op.drop_column('payments', 'fee_amount_in_cents')
    op.drop_column('payments', 'discount_amount_in_cents')
    op.drop_column('payments', 'subtotal_amount_in_cents')
    op.drop_index('ix_extra_services_professional_id', table_name='extra_services')
    op.drop_table('extra_services')
