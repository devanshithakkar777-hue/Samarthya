"""qualification kind, stream, awarding body

Revision ID: b7e2c1d4a9f0
Revises: a1c0de5f7e21
"""
from alembic import op
import sqlalchemy as sa

revision = "b7e2c1d4a9f0"
down_revision = "a1c0de5f7e21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("qualifications", sa.Column("kind", sa.String(40), nullable=False, server_default="degree"))
    op.add_column("qualifications", sa.Column("stream", sa.String(80), nullable=True))
    op.add_column("qualifications", sa.Column("awarding_body", sa.String(160), nullable=True))


def downgrade() -> None:
    for c in ("awarding_body", "stream", "kind"):
        op.drop_column("qualifications", c)
