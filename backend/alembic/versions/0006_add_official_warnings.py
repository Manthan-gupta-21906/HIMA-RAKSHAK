"""Add official warnings table for authoritative bulletins.

Revision ID: 0006_add_official_warnings
Revises: 0005_add_risk_assessments
Create Date: 2026-11-26 18:30:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0006_add_official_warnings"
down_revision = "0005_add_risk_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "official_warnings",
        sa.Column("warning_id", sa.String(length=64), primary_key=True),
        sa.Column("authority", sa.String(length=32), nullable=False),
        sa.Column("hazard_type", sa.String(length=32), nullable=False),
        sa.Column(
            "location_id",
            sa.String(length=32),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column("severity_label", sa.String(length=64), nullable=False),
        sa.Column("headline", sa.String(length=240), nullable=False),
        sa.Column("geographic_scope", sa.String(length=200), nullable=True),
        sa.Column("summary", sa.String(length=1000), nullable=True),
        sa.Column("advisory_notes", sa.String(length=1000), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("source_reference", sa.String(length=200), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "is_read_only",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("provenance", sa.String(length=160), nullable=False),
        sa.Column(
            "is_demo_fixture",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_official_warnings_authority", "official_warnings", ["authority"])
    op.create_index("ix_official_warnings_hazard_type", "official_warnings", ["hazard_type"])
    op.create_index("ix_official_warnings_location_id", "official_warnings", ["location_id"])
    op.create_index("ix_official_warnings_severity_label", "official_warnings", ["severity_label"])
    op.create_index("ix_official_warnings_issued_at", "official_warnings", ["issued_at"])
    op.create_index("ix_official_warnings_valid_until", "official_warnings", ["valid_until"])


def downgrade() -> None:
    op.drop_index("ix_official_warnings_valid_until", table_name="official_warnings")
    op.drop_index("ix_official_warnings_issued_at", table_name="official_warnings")
    op.drop_index("ix_official_warnings_severity_label", table_name="official_warnings")
    op.drop_index("ix_official_warnings_location_id", table_name="official_warnings")
    op.drop_index("ix_official_warnings_hazard_type", table_name="official_warnings")
    op.drop_index("ix_official_warnings_authority", table_name="official_warnings")
    op.drop_table("official_warnings")
