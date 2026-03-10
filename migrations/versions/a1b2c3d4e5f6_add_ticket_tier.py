"""add ticket_tier table and payment_intent tier snapshot columns

Revision ID: a1b2c3d4e5f6
Revises: b2f1a3c9d4e7
Create Date: 2026-03-10 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'b2f1a3c9d4e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Phase A — DDL

    op.create_table(
        'ticket_tier',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('event.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('available_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('available_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('required_person_status', postgresql.ENUM('pending', 'verified', 'rejected', 'member', name='personstatus', create_type=False), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('ecrm_good_code', sa.String(10), nullable=True),
        sa.Column('ecrm_good_name', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.add_column('payment_intent', sa.Column('tier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ticket_tier.id'), nullable=True))
    op.add_column('payment_intent', sa.Column('tier_price', sa.Integer(), nullable=True))

    # Phase B — Seed tiers from existing flat Event columns
    op.execute("""
        INSERT INTO ticket_tier (event_id, name, price, required_person_status, sort_order, is_active, ecrm_good_code, ecrm_good_name)
        SELECT
            id,
            'Member',
            member_ticket_price,
            'member',
            0,
            true,
            '0003',
            'Member Event Entry'
        FROM event
        WHERE member_ticket_price IS NOT NULL
    """)

    op.execute("""
        INSERT INTO ticket_tier (event_id, name, price, available_until, sort_order, is_active, ecrm_good_code, ecrm_good_name)
        SELECT
            id,
            'Early Bird',
            early_bird_price,
            early_bird_date,
            1,
            true,
            '0002',
            'Early Bird Event Entry'
        FROM event
        WHERE early_bird_price IS NOT NULL AND early_bird_date IS NOT NULL
    """)

    op.execute("""
        INSERT INTO ticket_tier (event_id, name, price, sort_order, is_active, ecrm_good_code, ecrm_good_name)
        SELECT
            id,
            'General Admission',
            general_admission_price,
            2,
            true,
            '0001',
            'General Admission Event Entry'
        FROM event
        WHERE general_admission_price IS NOT NULL
    """)


def downgrade() -> None:
    op.drop_column('payment_intent', 'tier_price')
    op.drop_column('payment_intent', 'tier_id')
    op.drop_table('ticket_tier')
