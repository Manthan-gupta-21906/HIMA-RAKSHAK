"""Authoritative warning ingestion and clearly labelled sample fixtures."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.official_warning import OfficialWarningModel
from app.schemas.common import HazardType
from app.schemas.warning import WarningAuthority, WarningCreate

NOW = datetime.now(UTC)

# Clearly labelled official warning sample fixtures (authoritative bulletins)
SAMPLE_WARNING_FIXTURES: list[dict] = [
  {
      "warning_id": "WARN-CWC-2026-104",
      "authority": WarningAuthority.CWC,
      "hazard_type": HazardType.FLOOD,
      "location_id": "loc-test-1",
      "severity_label": "Red",
      "headline": "Flash Flood Watch — Poonch & Surankote Tributaries",
      "geographic_scope": "Poonch - Surankote",
      "summary": (
          "Rapid rise observed on Surankote nallah and Poonch river gauge (17.80 ft vs 18.0 ft alert mark) "
          "following 68 mm rainfall in 6 hours."
      ),
      "advisory_notes": (
          "Authoritative CWC hydrological bulletin. Maintain continuous gauge watch along low-lying Surankote bridges "
          "and approach roads."
      ),
      "source_url": "https://cwc.gov.in/bulletins/north/2026-104",
      "source_reference": "CWC Northern Rivers Bulletin (Sample Cached Record)",
      "issued_at": NOW - timedelta(hours=4),
      "valid_until": NOW + timedelta(hours=14),
      "provenance": "official:cwc-bulletin-2026-104",
      "is_demo_fixture": True,
  },
  {
      "warning_id": "WARN-DGRE-2026-038",
      "authority": WarningAuthority.DGRE,
      "hazard_type": HazardType.AVALANCHE,
      "location_id": "loc-test-1",
      "severity_label": "Orange",
      "headline": "Stage-3 Avalanche Warning — Gulmarg & Affarwat Ridge",
      "geographic_scope": "Gulmarg - Affarwat Ridge",
      "summary": (
          "Medium-sized natural and triggered avalanches likely on steep slopes above 3,000 m following "
          "45 cm fresh snowfall and 60 km/h NW winds."
      ),
      "advisory_notes": (
          "Authoritative DGRE avalanche bulletin. Restrict movement on wind-loaded slopes >35 degrees."
      ),
      "source_url": "https://dgre.drdo.gov.in/avalanche/2026-038",
      "source_reference": "DGRE Chandigarh Avalanche Bulletin (Sample Cached Record)",
      "issued_at": NOW - timedelta(hours=8),
      "valid_until": NOW + timedelta(hours=16),
      "provenance": "official:dgre-bulletin-2026-038",
      "is_demo_fixture": True,
  },
  {
      "warning_id": "WARN-IMD-2026-219",
      "authority": WarningAuthority.IMD,
      "hazard_type": HazardType.FLOOD,
      "location_id": "loc-test-1",
      "severity_label": "Orange",
      "headline": "Heavy Precipitation & Catchment Runoff Advisory",
      "geographic_scope": "Kupwara & Bandipora Higher Catchments",
      "summary": (
          "Active Western Disturbance bringing heavy rainfall in river headwaters. Potential for rapid localized inundation."
      ),
      "advisory_notes": "Authoritative IMD Meteorological Centre Srinagar bulletin. Monitor river tributaries.",
      "source_url": "https://mausam.imd.gov.in/srinagar/warnings/219",
      "source_reference": "IMD MC Srinagar Nowcast/Bulletin (Sample Cached Record)",
      "issued_at": NOW - timedelta(hours=10),
      "valid_until": NOW + timedelta(hours=14),
      "provenance": "official:imd-bulletin-2026-219",
      "is_demo_fixture": True,
  },
  {
      "warning_id": "WARN-EXPIRED-SAMPLE-01",
      "authority": WarningAuthority.CWC,
      "hazard_type": HazardType.FLOOD,
      "location_id": "loc-test-1",
      "severity_label": "Yellow",
      "headline": "Past Advisory — Jhelum Basin Routine Advisory",
      "geographic_scope": "Jhelum Basin Upper Catchment",
      "summary": "Routine gauge monitoring advisory from yesterday that has already concluded.",
      "advisory_notes": "Authoritative historical bulletin kept for audit and provenance.",
      "source_url": "https://cwc.gov.in/bulletins/north/historical-01",
      "source_reference": "CWC Historical Advisory (Sample Cached Record)",
      "issued_at": NOW - timedelta(days=2),
      "valid_until": NOW - timedelta(days=1),
      "provenance": "official:cwc-historical-sample",
      "is_demo_fixture": True,
  },
]


def load_sample_warning_fixtures() -> list[WarningCreate]:
    """Parse and validate sample warning fixtures into WarningCreate contracts."""
    return [WarningCreate(**fixture) for fixture in SAMPLE_WARNING_FIXTURES]


def import_warning_record(db: Session, warning_data: WarningCreate | dict) -> OfficialWarningModel:
    """Import an authoritative warning preserving authority, validity, and verbatim content."""
    if isinstance(warning_data, dict):
        payload = WarningCreate(**warning_data)
    else:
        payload = warning_data

    existing = db.get(OfficialWarningModel, payload.warning_id)
    if existing:
        existing.authority = payload.authority.value
        existing.hazard_type = payload.hazard_type.value
        existing.location_id = payload.location_id
        existing.severity_label = payload.severity_label
        existing.headline = payload.headline
        existing.geographic_scope = payload.geographic_scope
        existing.summary = payload.summary
        existing.advisory_notes = payload.advisory_notes
        existing.source_url = payload.source_url
        existing.source_reference = payload.source_reference
        existing.issued_at = payload.issued_at
        existing.valid_until = payload.valid_until
        existing.provenance = payload.provenance
        existing.is_demo_fixture = payload.is_demo_fixture
        existing.ingested_at = datetime.now(UTC)
        db.flush()
        return existing

    model = OfficialWarningModel(
        warning_id=payload.warning_id,
        authority=payload.authority.value,
        hazard_type=payload.hazard_type.value,
        location_id=payload.location_id,
        severity_label=payload.severity_label,
        headline=payload.headline,
        geographic_scope=payload.geographic_scope,
        summary=payload.summary,
        advisory_notes=payload.advisory_notes,
        source_url=payload.source_url,
        source_reference=payload.source_reference,
        issued_at=payload.issued_at,
        valid_until=payload.valid_until,
        is_read_only=True,
        provenance=payload.provenance,
        is_demo_fixture=payload.is_demo_fixture,
        ingested_at=datetime.now(UTC),
    )
    db.add(model)
    db.flush()
    return model


def import_sample_fixtures(db: Session) -> list[OfficialWarningModel]:
    """Load and ingest all clearly labelled sample warning fixtures."""
    fixtures = load_sample_warning_fixtures()
    results = [import_warning_record(db, item) for item in fixtures]
    db.commit()
    return results
