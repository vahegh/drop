"""drop event flat pricing fields

Revision ID: d4e5f6a7b8c9
Revises: b63c2a01de3b
Create Date: 2026-03-12 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'b63c2a01de3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('event', 'early_bird_date')
    op.drop_column('event', 'early_bird_price')
    op.drop_column('event', 'general_admission_price')
    op.drop_column('event', 'member_ticket_price')


def downgrade() -> None:
    op.add_column('event', sa.Column('member_ticket_price', sa.Integer(), nullable=True))
    op.add_column('event', sa.Column('general_admission_price', sa.Integer(), nullable=True))
    op.add_column('event', sa.Column('early_bird_price', sa.Integer(), nullable=True))
    op.add_column('event', sa.Column('early_bird_date', sa.DateTime(timezone=True), nullable=True))
