"""Add expanded_queries and monitoring_frequency to site_profiles

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "site_profiles",
        sa.Column("expanded_queries", sa.JSON(), nullable=True),
    )
    op.add_column(
        "site_profiles",
        sa.Column(
            "monitoring_frequency",
            sa.String(),
            nullable=False,
            server_default="weekly",
        ),
    )


def downgrade() -> None:
    op.drop_column("site_profiles", "expanded_queries")
    op.drop_column("site_profiles", "monitoring_frequency")
