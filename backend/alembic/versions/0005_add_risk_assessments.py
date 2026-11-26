"""Add risk assessments table for multi-hazard risk states.

Revision ID: 0005_add_risk_assessments
Revises: 0004_add_observations
Create Date: 2026-11-26 17:15:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0005_add_risk_assessments"
down_revision = "0004_add_observations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risk_assessments",
        sa.Column("risk_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "location_id",
            sa.String(length=32),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column("hazard_type", sa.String(length=32), nullable=False),
        sa.Column("risk_class", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("lead_time_hours", sa.Integer(), nullable=False),
        sa.Column("freshness", sa.String(length=32), nullable=False),
        sa.Column("prediction_status", sa.String(length=32), nullable=False),
        sa.Column("readiness_reason", sa.String(length=300), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=True),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("licence", sa.String(length=120), nullable=False),
        sa.Column(
            "is_demo_fixture",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "location_id",
            "hazard_type",
            "assessed_at",
            name="uq_risk_assessment_location_hazard_time",
        ),
    )
    op.create_index("ix_risk_assessments_location_id", "risk_assessments", ["location_id"])
    op.create_index("ix_risk_assessments_hazard_type", "risk_assessments", ["hazard_type"])
    op.create_index("ix_risk_assessments_risk_class", "risk_assessments", ["risk_class"])
    op.create_index(
        "ix_risk_assessments_prediction_status", "risk_assessments", ["prediction_status"]
    )
    op.create_index("ix_risk_assessments_assessed_at", "risk_assessments", ["assessed_at"])


def downgrade() -> None:
    op.drop_index("ix_risk_assessments_assessed_at", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_prediction_status", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_risk_class", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_hazard_type", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_location_id", table_name="risk_assessments")
    op.drop_table("risk_assessments")
