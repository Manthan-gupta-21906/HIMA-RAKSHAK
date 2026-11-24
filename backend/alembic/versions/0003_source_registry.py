"""Add source registry columns for provider, dataset, access_mode, and freshness.

Revision ID: 0003_source_registry
Revises: 0002_add_users
Create Date: 2026-11-25 01:30:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_source_registry"
down_revision = "0002_add_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sources") as batch_op:
        batch_op.add_column(
            sa.Column(
                "provider",
                sa.String(120),
                nullable=False,
                server_default="Unknown Provider",
            )
        )
        batch_op.add_column(
            sa.Column(
                "dataset",
                sa.String(120),
                nullable=False,
                server_default="Unknown Dataset",
            )
        )
        batch_op.add_column(
            sa.Column(
                "access_mode",
                sa.String(16),
                nullable=False,
                server_default="sample",
            )
        )
        batch_op.add_column(
            sa.Column(
                "trust_classification",
                sa.String(32),
                nullable=False,
                server_default="demo",
            )
        )
        batch_op.add_column(
            sa.Column(
                "reference_url",
                sa.String(500),
                nullable=False,
                server_default="",
            )
        )
        batch_op.add_column(
            sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.create_index("ix_sources_access_mode", ["access_mode"])

    # Backfill with source_name if possible
    op.execute(
        "UPDATE sources SET provider = source_name WHERE provider = 'Unknown Provider'"
    )
    op.execute(
        "UPDATE sources SET dataset = source_name WHERE dataset = 'Unknown Dataset'"
    )


def downgrade() -> None:
    with op.batch_alter_table("sources") as batch_op:
        batch_op.drop_index("ix_sources_access_mode")
        batch_op.drop_column("last_fetched_at")
        batch_op.drop_column("reference_url")
        batch_op.drop_column("trust_classification")
        batch_op.drop_column("access_mode")
        batch_op.drop_column("dataset")
        batch_op.drop_column("provider")
