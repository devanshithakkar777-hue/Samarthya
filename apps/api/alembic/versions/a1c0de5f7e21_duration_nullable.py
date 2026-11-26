"""qualification duration may be unknown

Revision ID: a1c0de5f7e21
Revises: 26d726830fc4
Create Date: 2026-11-26 21:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "a1c0de5f7e21"
down_revision = "26d726830fc4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("qualifications", "duration_years", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE qualifications SET duration_years = 3 WHERE duration_years IS NULL")
    op.alter_column("qualifications", "duration_years", existing_type=sa.Integer(), nullable=False)
