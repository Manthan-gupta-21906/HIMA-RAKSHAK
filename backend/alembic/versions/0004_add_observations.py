"""Add observations table for time-series environmental data.

Revision ID: 0004_add_observations
Revises: 0003_source_registry
Create Date: 2026-11-25 01:50:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0004_add_observations"
down_revision = "0003_source_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "observations",
        sa.Column("observation_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "location_id",
            sa.String(length=32),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            sa.String(length=64),
            sa.ForeignKey("sources.source_id"),
            nullable=False,
        ),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metric", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column(
            "is_demo_fixture",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "location_id",
            "source_id",
            "observed_at",
            "metric",
            name="uq_observations_natural_key",
        ),
    )
    op.create_index("ix_observations_location_id", "observations", ["location_id"])
    op.create_index("ix_observations_source_id", "observations", ["source_id"])
    op.create_index("ix_observations_observed_at", "observations", ["observed_at"])
    op.create_index("ix_observations_metric", "observations", ["metric"])
    op.create_index(
        "ix_observations_idempotency_key",
        "observations",
        ["idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_observations_idempotency_key", table_name="observations")
    op.drop_index("ix_observations_metric", table_name="observations")
    op.drop_index("ix_observations_observed_at", table_name="observations")
    op.drop_index("ix_observations_source_id", table_name="observations")
    op.drop_index("ix_observations_location_id", table_name="observations")
    op.drop_table("observations")
