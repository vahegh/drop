"""rename person.drive_folder_url to album_url

Revision ID: b2f1a3c9d4e7
Revises: e6773717baaa
Create Date: 2026-03-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b2f1a3c9d4e7'
down_revision: Union[str, None] = 'e6773717baaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('person', 'drive_folder_url', new_column_name='album_url')


def downgrade() -> None:
    op.alter_column('person', 'album_url', new_column_name='drive_folder_url')
