"""Merge lockout and activity migrations

Revision ID: c0b0103d85ef
Revises: 481039a32713, a1b2c3d4e5f6
Create Date: 2026-04-03 00:11:33.546379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0b0103d85ef'
down_revision: Union[str, Sequence[str], None] = ('481039a32713', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
