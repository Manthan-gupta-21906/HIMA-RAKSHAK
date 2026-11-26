"""Alembic migration for ingestion runs monitoring and retry tracking.

Revision ID: 0010_add_ingestion_runs
Revises: 0009_add_alert_deliveries
Create Date: 2026-11-26 20:25:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0010_add_ingestion_runs"
down_revision = "0009_add_alert_deliveries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("run_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "source_id",
            sa.String(length=64),
            sa.ForeignKey("sources.source_id"),
            nullable=False,
        ),
        sa.Column(
            "trigger_mode",
            sa.String(length=16),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("records_ingested", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ingestion_runs_source_id", "ingestion_runs", ["source_id"])
    op.create_index("ix_ingestion_runs_status", "ingestion_runs", ["status"])
    op.create_index("ix_ingestion_runs_started_at", "ingestion_runs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_runs_started_at", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_runs_status", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_runs_source_id", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
