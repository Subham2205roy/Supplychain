"""add_company_id

Revision ID: 30499e733cdb
Revises: c0b0103d85ef
Create Date: 2026-05-27 22:30:45.755838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30499e733cdb'
down_revision: Union[str, Sequence[str], None] = 'c0b0103d85ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First ensure a default company exists if not already
    op.execute(
        "INSERT INTO companies (id, name, owner_user_id) "
        "SELECT 1, 'Default Company', 1 "
        "WHERE NOT EXISTS (SELECT 1 FROM companies WHERE id = 1)"
    )

    tables = ['sales', 'inventory', 'suppliers', 'customers']
    
    for table in tables:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column('company_id', sa.Integer(), nullable=True))
        
        # Set default value for existing rows
        op.execute(f"UPDATE {table} SET company_id = 1 WHERE company_id IS NULL")
        
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column('company_id', existing_type=sa.Integer(), nullable=False)
            batch_op.create_foreign_key(f"fk_{table}_company_id", 'companies', ['company_id'], ['id'])
            batch_op.create_index(batch_op.f(f'ix_{table}_company_id'), ['company_id'], unique=False)

    # Add unique constraint to sales
    with op.batch_alter_table('sales', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_sales_company_order', ['company_id', 'order_id'])


def downgrade() -> None:
    with op.batch_alter_table('sales', schema=None) as batch_op:
        batch_op.drop_constraint('uq_sales_company_order', type_='unique')

    tables = ['sales', 'inventory', 'suppliers', 'customers']
    for table in reversed(tables):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_index(batch_op.f(f'ix_{table}_company_id'))
            batch_op.drop_constraint(f"fk_{table}_company_id", type_='foreignkey')
            batch_op.drop_column('company_id')
