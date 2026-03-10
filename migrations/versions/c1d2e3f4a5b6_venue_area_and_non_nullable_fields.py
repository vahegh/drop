"""venue area field and non-nullable location fields

Revision ID: c1d2e3f4a5b6
Revises: b2f1a3c9d4e7
Create Date: 2026-03-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'b2f1a3c9d4e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add area column as nullable first
    op.add_column('venue', sa.Column('area', sa.String(), nullable=True))

    # Set defaults on any rows with nulls before tightening constraints
    op.execute("UPDATE venue SET area = '' WHERE area IS NULL")
    op.execute("UPDATE venue SET address = '' WHERE address IS NULL")
    op.execute("UPDATE venue SET latitude = 0 WHERE latitude IS NULL")
    op.execute("UPDATE venue SET longitude = 0 WHERE longitude IS NULL")

    # Make all location fields non-nullable
    op.alter_column('venue', 'area', nullable=False)
    op.alter_column('venue', 'address', nullable=False)
    op.alter_column('venue', 'latitude', nullable=False)
    op.alter_column('venue', 'longitude', nullable=False)


def downgrade() -> None:
    op.alter_column('venue', 'address', nullable=True)
    op.alter_column('venue', 'latitude', nullable=True)
    op.alter_column('venue', 'longitude', nullable=True)
    op.drop_column('venue', 'area')
