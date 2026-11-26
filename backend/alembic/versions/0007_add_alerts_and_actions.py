"""Alembic migration for system alerts and operator action history.

Revision ID: 0007_add_alerts_and_actions
Revises: 0006_add_official_warnings
Create Date: 2026-11-26 19:25:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0007_add_alerts_and_actions"
down_revision = "0006_add_official_warnings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("alert_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "location_id",
            sa.String(length=32),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column("hazard_type", sa.String(length=32), nullable=False),
        sa.Column(
            "risk_id",
            sa.String(length=64),
            sa.ForeignKey("risk_assessments.risk_id"),
            nullable=True,
        ),
        sa.Column("priority_level", sa.String(length=32), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("acknowledged_by", sa.String(length=64), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("action_note", sa.Text(), nullable=True),
        sa.Column("action_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_official_warning",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alerts_location_id", "alerts", ["location_id"])
    op.create_index("ix_alerts_hazard_type", "alerts", ["hazard_type"])
    op.create_index("ix_alerts_priority_level", "alerts", ["priority_level"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_alerts_created_at", table_name="alerts")
    op.drop_index("ix_alerts_status", table_name="alerts")
    op.drop_index("ix_alerts_priority_level", table_name="alerts")
    op.drop_index("ix_alerts_hazard_type", table_name="alerts")
    op.drop_index("ix_alerts_location_id", table_name="alerts")
    op.drop_table("alerts")
