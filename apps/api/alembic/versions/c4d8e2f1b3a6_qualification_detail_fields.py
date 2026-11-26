"""qualification detail fields

Revision ID: c4d8e2f1b3a6
Revises: b7e2c1d4a9f0
"""
from alembic import op
import sqlalchemy as sa

revision = "c4d8e2f1b3a6"
down_revision = "b7e2c1d4a9f0"
branch_labels = None
depends_on = None
TEXT = ("eligibility", "entry_route", "training", "recognition", "cost_note")


def upgrade() -> None:
    for c in TEXT:
        op.add_column("qualifications", sa.Column(c, sa.Text(), nullable=True))
    op.add_column("qualifications", sa.Column("official_url", sa.String(300), nullable=True))


def downgrade() -> None:
    for c in ("official_url",) + TEXT:
        op.drop_column("qualifications", c)
