"""Initial Location and Source persistence with PostGIS support.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-25 00:45:00
"""

import sqlalchemy as sa
from geoalchemy2 import Geometry

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "sources",
        sa.Column("source_id", sa.String(length=64), primary_key=True),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("licence", sa.String(length=120), nullable=False),
        sa.Column("update_frequency_minutes", sa.Integer(), nullable=False),
        sa.Column("is_authoritative", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_demo_fixture", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sources_source_type", "sources", ["source_type"])

    geom_type = Geometry("POINT", srid=4326) if is_postgres else sa.Text()
    op.create_table(
        "locations",
        sa.Column("location_id", sa.String(length=32), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("admin_unit", sa.String(length=120), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("geom", geom_type, nullable=False),
        sa.Column("supported_hazards", sa.JSON(), nullable=False),
        sa.Column("coverage_status", sa.String(length=24), nullable=False),
        sa.Column("coverage_note", sa.Text(), nullable=False),
        sa.Column("is_demo_fixture", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("provenance", sa.String(length=120), nullable=False),
    )
    op.create_index("ix_locations_admin_unit", "locations", ["admin_unit"])
    op.create_index("ix_locations_coverage_status", "locations", ["coverage_status"])
    if is_postgres:
        op.create_index(
            "ix_locations_geom", "locations", ["geom"], postgresql_using="gist"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_index("ix_locations_geom", table_name="locations")
    op.drop_index("ix_locations_coverage_status", table_name="locations")
    op.drop_index("ix_locations_admin_unit", table_name="locations")
    op.drop_table("locations")
    op.drop_index("ix_sources_source_type", table_name="sources")
    op.drop_table("sources")
