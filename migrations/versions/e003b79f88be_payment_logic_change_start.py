"""payment logic change start

Revision ID: e003b79f88be
Revises: dd804e193a1d
Create Date: 2025-09-24 02:55:23.894889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e003b79f88be'
down_revision: Union[str, None] = 'dd804e193a1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table('payment', 'payment_old')


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table('payment_old', 'payment')
