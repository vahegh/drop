"""venue non-nullable location fields and event area field

Revision ID: c1d2e3f4a5b6
Revises: b2f1a3c9d4e7
Create Date: 2026-03-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make venue location fields non-nullable
    op.execute("UPDATE venue SET address = '' WHERE address IS NULL")
    op.execute("UPDATE venue SET latitude = 0 WHERE latitude IS NULL")
    op.execute("UPDATE venue SET longitude = 0 WHERE longitude IS NULL")
    op.alter_column('venue', 'address', nullable=False)
    op.alter_column('venue', 'latitude', nullable=False)
    op.alter_column('venue', 'longitude', nullable=False)

    # Add area to event (nullable - existing events won't have it)
    op.add_column('event', sa.Column('area', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('event', 'area')
    op.alter_column('venue', 'address', nullable=True)
    op.alter_column('venue', 'latitude', nullable=True)
    op.alter_column('venue', 'longitude', nullable=True)
