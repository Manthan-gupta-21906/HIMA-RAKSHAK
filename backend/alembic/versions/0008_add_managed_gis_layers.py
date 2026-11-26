"""Alembic migration for managed GIS layers table.

Revision ID: 0008_add_managed_gis_layers
Revises: 0007_add_alerts_and_actions
Create Date: 2026-11-26 20:15:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0008_add_managed_gis_layers"
down_revision = "0007_add_alerts_and_actions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "managed_gis_layers",
        sa.Column("layer_id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "layer_category",
            sa.String(length=32),
            nullable=False,
            server_default="exposure",
        ),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("provenance", sa.String(length=200), nullable=False),
        sa.Column(
            "is_demo_fixture",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("source_crs_epsg", sa.Integer(), nullable=False, server_default="4326"),
        sa.Column("feature_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("geojson", sa.JSON(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_managed_gis_layers_category", "managed_gis_layers", ["layer_category"]
    )
    op.create_index("ix_managed_gis_layers_active", "managed_gis_layers", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_managed_gis_layers_active", table_name="managed_gis_layers")
    op.drop_index("ix_managed_gis_layers_category", table_name="managed_gis_layers")
    op.drop_table("managed_gis_layers")
