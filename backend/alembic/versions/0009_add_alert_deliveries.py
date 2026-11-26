"""Alembic migration for alert delivery tracking.

Revision ID: 0009_add_alert_deliveries
Revises: 0008_add_managed_gis_layers
Create Date: 2026-11-26 20:20:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0009_add_alert_deliveries"
down_revision = "0008_add_managed_gis_layers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "alerts",
        sa.Column(
            "delivery_status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
    )
    op.create_index("ix_alerts_delivery_status", "alerts", ["delivery_status"])

    op.create_table(
        "alert_deliveries",
        sa.Column("delivery_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "alert_id",
            sa.String(length=64),
            sa.ForeignKey("alerts.alert_id"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("target", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alert_deliveries_alert_id", "alert_deliveries", ["alert_id"])
    op.create_index("ix_alert_deliveries_channel", "alert_deliveries", ["channel"])
    op.create_index("ix_alert_deliveries_status", "alert_deliveries", ["status"])
    op.create_index(
        "ix_alert_deliveries_created_at", "alert_deliveries", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_alert_deliveries_created_at", table_name="alert_deliveries")
    op.drop_index("ix_alert_deliveries_status", table_name="alert_deliveries")
    op.drop_index("ix_alert_deliveries_channel", table_name="alert_deliveries")
    op.drop_index("ix_alert_deliveries_alert_id", table_name="alert_deliveries")
    op.drop_table("alert_deliveries")
    op.drop_index("ix_alerts_delivery_status", table_name="alerts")
    op.drop_column("alerts", "delivery_status")
