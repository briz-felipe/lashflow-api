"""initial_schema

Revision ID: ae4721e425b2
Revises: 
Create Date: 2026-03-16 14:46:21.031320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'ae4721e425b2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # If tables already exist (DB was created by create_db_and_tables before Alembic was
    # introduced), skip this migration entirely — alembic stamp head was run on the server.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'users' in inspector.get_table_names():
        return

    # Correct dependency order:
    # users → procedures → clients
    #                    → appointments (without payment_id FK for now)
    #                    → payments     (depends on appointments + clients)
    #                    → appointments.payment_id FK added after (circular)
    # users → materials → stock_movements
    # users → blocked_dates, expenses, time_slots
    # payments → partial_payment_records
    # clients → anamneses

    op.create_table('users',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('username', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('password_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    op.create_table('procedures',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('professional_id', sa.Uuid(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('price_in_cents', sa.Integer(), nullable=False),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('image_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['professional_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedures_professional_id'), 'procedures', ['professional_id'], unique=False)

    op.create_table('clients',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('professional_id', sa.Uuid(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
    sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('instagram', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.Column('birthday', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('address', sa.JSON(), nullable=True),
    sa.Column('segments', sa.JSON(), nullable=True),
    sa.Column('favorite_procedure_id', sa.Uuid(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['favorite_procedure_id'], ['procedures.id'], ),
    sa.ForeignKeyConstraint(['professional_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clients_phone'), 'clients', ['phone'], unique=False)
    op.create_index(op.f('ix_clients_professional_id'), 'clients', ['professional_id'], unique=False)

    # appointments without payment_id FK (circular dep — added after payments is created)
    op.create_table('appointments',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('professional_id', sa.Uuid(), nullable=False),
    sa.Column('client_id', sa.Uuid(), nullable=False),
    sa.Column('procedure_id', sa.Uuid(), nullable=False),
    sa.Column('payment_id', sa.Uuid(), nullable=True),
    sa.Column('service_type', sa.Enum('application', 'maintenance', 'removal', 'lash_lifting', 'permanent', name='lashservicetype'), nullable=True),
    sa.Column('status', sa.Enum('pending_approval', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show', name='appointmentstatus'), nullable=False),
    sa.Column('scheduled_at', sa.DateTime(), nullable=False),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('price_charged', sa.Integer(), nullable=False),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('requested_at', sa.DateTime(), nullable=False),
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(), nullable=True),
    sa.Column('cancellation_reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('cancelled_by', sa.Enum('professional', 'client', name='cancelledby'), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['procedure_id'], ['procedures.id'], ),
    sa.ForeignKeyConstraint(['professional_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointments_client_id'), 'appointments', ['client_id'], unique=False)
    op.create_index(op.f('ix_appointments_procedure_id'), 'appointments', ['procedure_id'], unique=False)
    op.create_index(op.f('ix_appointments_professional_id'), 'appointments', ['professional_id'], unique=False)
    op.create_index(op.f('ix_appointments_scheduled_at'), 'appointments', ['scheduled_at'], unique=False)
    op.create_index(op.f('ix_appointments_status'), 'appointments', ['status'], unique=False)

    op.create_table('payments',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('professional_id', sa.Uuid(), nullable=False),
    sa.Column('appointment_id', sa.Uuid(), nullable=False),
    sa.Column('client_id', sa.Uuid(), nullable=False),
    sa.Column('total_amount_in_cents', sa.Integer(), nullable=False),
    sa.Column('paid_amount_in_cents', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'paid', 'partial', 'refunded', 'failed', name='paymentstatus'), nullable=False),
    sa.Column('method', sa.Enum('cash', 'credit_card', 'debit_card', 'pix', 'bank_transfer', 'other', name='paymentmethod'), nullable=True),
    sa.Column('paid_at', sa.DateTime(), nullable=True),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['professional_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_appointment_id'), 'payments', ['appointment_id'], unique=True)
    op.create_index(op.f('ix_payments_client_id'), 'payments', ['client_id'], unique=False)
    op.create_index(op.f('ix_payments_professional_id'), 'payments', ['professional_id'], unique=False)

    # Close the circular FK: appointments.payment_id → payments
    op.create_foreign_key(None, 'appointments', 'payments', ['payment_id'], ['id'])

    op.create_table('blocked_dates',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('professional_id', sa.Uuid(), nullable=False),
    sa.Column('date', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
    sa.Column('reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['professional_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blocked_dates_date'), 'blocked_dates', ['date'], unique=False)
    op.create_index(op.f('ix_blocked_dates_professional_id'), 'blocked_dates', ['professional_id'], unique=False)

    op.create_table('expenses',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('professional_id', sa.Uuid(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
    sa.Column('category', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('amount_in_cents', sa.Integer(), nullable=False),
    sa.Column('recurrence', sa.Enum('one_time', 'monthly', 'weekly', 'yearly', name='expenserecurrence'), nullable=False),
    sa.Column('due_day', sa.Integer(), nullable=True),
    sa.Column('is_paid', sa.Boolean(), nullable=False),
    sa.Column('paid_at', sa.DateTime(), nullable=True),
    sa.Column('reference_month', sqlmodel.sql.sqltypes.AutoString(length=7), nullable=False),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('installment_total', sa.Integer(), nullable=True),
    sa.Column('installment_current', sa.Integer(), nullable=True),
    sa.Column('installment_group_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['professional_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expenses_installment_group_id'), 'expenses', ['installment_group_id'], unique=False)
    op.create_index(op.f('ix_expenses_professional_id'), 'expenses', ['professional_id'], unique=False)
    op.create_index(op.f('ix_expenses_reference_month'), 'expenses', ['reference_month'], unique=False)

    op.create_table('materials',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('professional_id', sa.Uuid(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
    sa.Column('category', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('unit', sa.Enum('un', 'pacote', 'caixa', 'ml', 'g', 'par', 'rolo', 'kit', name='materialunit'), nullable=False),
    sa.Column('unit_cost_in_cents', sa.Integer(), nullable=False),
    sa.Column('current_stock', sa.Integer(), nullable=False),
    sa.Column('minimum_stock', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['professional_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_materials_professional_id'), 'materials', ['professional_id'], unique=False)

    op.create_table('time_slots',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('professional_id', sa.Uuid(), nullable=False),
    sa.Column('day_of_week', sa.Integer(), nullable=False),
    sa.Column('start_time', sqlmodel.sql.sqltypes.AutoString(length=5), nullable=False),
    sa.Column('end_time', sqlmodel.sql.sqltypes.AutoString(length=5), nullable=False),
    sa.Column('is_available', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['professional_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_time_slots_professional_id'), 'time_slots', ['professional_id'], unique=False)

    op.create_table('partial_payment_records',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('payment_id', sa.Uuid(), nullable=False),
    sa.Column('amount_in_cents', sa.Integer(), nullable=False),
    sa.Column('method', sa.Enum('cash', 'credit_card', 'debit_card', 'pix', 'bank_transfer', 'other', name='paymentmethod'), nullable=False),
    sa.Column('paid_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_partial_payment_records_payment_id'), 'partial_payment_records', ['payment_id'], unique=False)

    op.create_table('stock_movements',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('professional_id', sa.Uuid(), nullable=False),
    sa.Column('material_id', sa.Uuid(), nullable=False),
    sa.Column('type', sa.Enum('purchase', 'usage', 'adjustment', name='stockmovementtype'), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('unit_cost_in_cents', sa.Integer(), nullable=False),
    sa.Column('total_cost_in_cents', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
    sa.ForeignKeyConstraint(['professional_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_movements_date'), 'stock_movements', ['date'], unique=False)
    op.create_index(op.f('ix_stock_movements_material_id'), 'stock_movements', ['material_id'], unique=False)
    op.create_index(op.f('ix_stock_movements_professional_id'), 'stock_movements', ['professional_id'], unique=False)

    op.create_table('anamneses',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('professional_id', sa.Uuid(), nullable=False),
    sa.Column('client_id', sa.Uuid(), nullable=False),
    sa.Column('has_allergy', sa.Boolean(), nullable=False),
    sa.Column('allergy_details', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('had_eye_surgery_last_3_months', sa.Boolean(), nullable=False),
    sa.Column('has_eye_disease', sa.Boolean(), nullable=False),
    sa.Column('eye_disease_details', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('uses_eye_drops', sa.Boolean(), nullable=False),
    sa.Column('family_thyroid_history', sa.Boolean(), nullable=False),
    sa.Column('has_glaucoma', sa.Boolean(), nullable=False),
    sa.Column('hair_loss_grade', sa.Enum('low', 'medium', 'high', name='anamnesishairloss'), nullable=True),
    sa.Column('prone_to_blepharitis', sa.Boolean(), nullable=False),
    sa.Column('has_epilepsy', sa.Boolean(), nullable=False),
    sa.Column('procedure_type', sa.Enum('extension', 'permanent', 'lash_lifting', name='anamnosisproceduretype'), nullable=False),
    sa.Column('mapping', sa.JSON(), nullable=True),
    sa.Column('authorized_photo_publishing', sa.Boolean(), nullable=False),
    sa.Column('signed_at', sa.DateTime(), nullable=True),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['professional_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_anamneses_client_id'), 'anamneses', ['client_id'], unique=False)
    op.create_index(op.f('ix_anamneses_professional_id'), 'anamneses', ['professional_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_anamneses_professional_id'), table_name='anamneses')
    op.drop_index(op.f('ix_anamneses_client_id'), table_name='anamneses')
    op.drop_table('anamneses')
    op.drop_index(op.f('ix_stock_movements_professional_id'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_material_id'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_date'), table_name='stock_movements')
    op.drop_table('stock_movements')
    op.drop_index(op.f('ix_partial_payment_records_payment_id'), table_name='partial_payment_records')
    op.drop_table('partial_payment_records')
    op.drop_index(op.f('ix_time_slots_professional_id'), table_name='time_slots')
    op.drop_table('time_slots')
    op.drop_index(op.f('ix_expenses_reference_month'), table_name='expenses')
    op.drop_index(op.f('ix_expenses_professional_id'), table_name='expenses')
    op.drop_index(op.f('ix_expenses_installment_group_id'), table_name='expenses')
    op.drop_table('expenses')
    op.drop_index(op.f('ix_blocked_dates_professional_id'), table_name='blocked_dates')
    op.drop_index(op.f('ix_blocked_dates_date'), table_name='blocked_dates')
    op.drop_table('blocked_dates')
    op.drop_index(op.f('ix_materials_professional_id'), table_name='materials')
    op.drop_table('materials')
    # Drop circular FK before dropping appointments/payments
    op.drop_constraint('appointments_payment_id_fkey', 'appointments', type_='foreignkey')
    op.drop_index(op.f('ix_payments_professional_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_client_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_appointment_id'), table_name='payments')
    op.drop_table('payments')
    op.drop_index(op.f('ix_appointments_status'), table_name='appointments')
    op.drop_index(op.f('ix_appointments_scheduled_at'), table_name='appointments')
    op.drop_index(op.f('ix_appointments_professional_id'), table_name='appointments')
    op.drop_index(op.f('ix_appointments_procedure_id'), table_name='appointments')
    op.drop_index(op.f('ix_appointments_client_id'), table_name='appointments')
    op.drop_table('appointments')
    op.drop_index(op.f('ix_clients_professional_id'), table_name='clients')
    op.drop_index(op.f('ix_clients_phone'), table_name='clients')
    op.drop_table('clients')
    op.drop_index(op.f('ix_procedures_professional_id'), table_name='procedures')
    op.drop_table('procedures')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
