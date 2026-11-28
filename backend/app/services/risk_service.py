"""Service layer for executing and querying multi-hazard risk assessments."""

from datetime import UTC, datetime

from app.features.avalanche import extract_avalanche_features
from app.features.flood import extract_flood_features
from app.features.metadata import FeatureValue, TerrainContext
from app.flood.model import FloodBaselineClassifier
from app.repositories.location_repository import SqlAlchemyLocationRepository
from app.repositories.observation_repository import ObservationRepository
from app.repositories.risk_repository import RiskAssessmentRepository
from app.repositories.source_repository import SourceRepository
from app.schemas.common import HazardType, ProvenanceMeta, RiskClass, ensure_timezone_aware
from app.schemas.risk import (
    LocationRiskState,
    ReplayEventContract,
    ReplayEventsResponse,
    ReplayFrameContract,
    RiskAssessmentContract,
)
from app.services.location_service import LocationNotFoundError
from app.services.observation_service import model_to_contract
from app.services.risk_orchestrator import RiskOrchestrator


class RiskService:
    """Service layer for executing, persisting, and querying risk assessments."""

    def __init__(
        self,
        risk_repo: RiskAssessmentRepository,
        observation_repo: ObservationRepository | None = None,
        location_repo: SqlAlchemyLocationRepository | None = None,
        source_repo: SourceRepository | None = None,
        flood_model: FloodBaselineClassifier | None = None,
    ) -> None:
        self._risk_repo = risk_repo
        self._observation_repo = observation_repo or ObservationRepository(risk_repo.session)
        self._location_repo = location_repo or SqlAlchemyLocationRepository(risk_repo.session)
        self._source_repo = source_repo or SourceRepository(risk_repo.session)
        self._flood_model = flood_model
        self._orchestrator = RiskOrchestrator(risk_repo)

    def _build_provenance(
        self,
        features: list[FeatureValue],
        sources_by_id: dict[str, object],
        assessed_at: datetime,
    ) -> ProvenanceMeta:
        """Build truthful provenance from referenced observation sources."""
        referenced_ids: list[str] = []
        for feat in features:
            for sid in feat.source_ids:
                if sid not in referenced_ids:
                    referenced_ids.append(sid)

        for sid in referenced_ids:
            src = sources_by_id.get(sid)
            if src is not None:
                return ProvenanceMeta(
                    source_id=src.source_id,  # type: ignore[attr-defined]
                    source_name=src.source_name,  # type: ignore[attr-defined]
                    licence=src.licence,  # type: ignore[attr-defined]
                    is_demo_fixture=src.is_demo_fixture,  # type: ignore[attr-defined]
                    ingested_at=assessed_at,
                )

        return ProvenanceMeta(
            source_id="internal-pipeline",
            source_name="HIMA-RAKSHAK Assessment Pipeline",
            licence="Internal System",
            is_demo_fixture=False,
            ingested_at=assessed_at,
        )

    def assess_location_risk(
        self,
        location_id: str,
        cutoff_at: datetime | None = None,
        flood_model: FloodBaselineClassifier | None = None,
        terrain: TerrainContext | None = None,
        historical_event_labels_count: int = 0,
        historical_non_event_labels_count: int = 0,
    ) -> LocationRiskState:
        """Execute independent flood and avalanche risk assessments for a location."""
        location = self._location_repo.get_by_id(location_id)
        if location is None:
            raise LocationNotFoundError(f"Location '{location_id}' not found.")

        effective_cutoff = (
            ensure_timezone_aware(cutoff_at) if cutoff_at is not None else datetime.now(UTC)
        )

        obs_models = self._observation_repo.list_by_location(location_id)
        obs_contracts = [model_to_contract(m) for m in obs_models]

        sources = self._source_repo.list_all()
        sources_by_id = {s.source_id: s for s in sources}
        source_cadences = {s.source_id: s.update_frequency_minutes for s in sources}

        selected_model = flood_model if flood_model is not None else self._flood_model
        fitted_model = (
            selected_model
            if selected_model is not None and bool(selected_model.weights)
            else None
        )

        supported = {
            h.value if isinstance(h, HazardType) else str(h).lower()
            for h in location.supported_hazards
        }

        if HazardType.FLOOD.value in supported:
            flood_features = extract_flood_features(
                location_id=location_id,
                observations=obs_contracts,
                cutoff_at=effective_cutoff,
                terrain=terrain,
                source_cadences=source_cadences,
            )
            flood_provenance = self._build_provenance(
                [
                    flood_features.rain_1h_mm,
                    flood_features.rain_24h_mm,
                    flood_features.antecedent_rain_72h_mm,
                    flood_features.river_level_m,
                    flood_features.river_level_rate_m_per_h,
                ],
                sources_by_id,
                effective_cutoff,
            )
            self._orchestrator.assess_flood(
                features=flood_features,
                model=fitted_model,
                source_meta=flood_provenance,
            )

        if HazardType.AVALANCHE.value in supported:
            avalanche_features = extract_avalanche_features(
                location_id=location_id,
                observations=obs_contracts,
                cutoff_at=effective_cutoff,
                terrain=terrain,
                source_cadences=source_cadences,
            )
            avalanche_provenance = self._build_provenance(
                [
                    avalanche_features.new_snow_24h_cm,
                    avalanche_features.snow_depth_cm,
                    avalanche_features.swe_estimate_mm,
                    avalanche_features.temp_mean_24h_c,
                    avalanche_features.wind_loading_kmh,
                ],
                sources_by_id,
                effective_cutoff,
            )
            self._orchestrator.assess_avalanche(
                features=avalanche_features,
                historical_event_labels_count=historical_event_labels_count,
                historical_non_event_labels_count=historical_non_event_labels_count,
                source_meta=avalanche_provenance,
            )

        return self._orchestrator.get_location_risk_state(location_id)

    def get_current_risk(
        self, location_id: str
    ) -> dict[str, RiskAssessmentContract | None]:
        """Return latest assessment for each hazard type for a location."""
        return {
            HazardType.FLOOD.value: self._risk_repo.get_latest_for_location_and_hazard(
                location_id, HazardType.FLOOD
            ),
            HazardType.AVALANCHE.value: self._risk_repo.get_latest_for_location_and_hazard(
                location_id, HazardType.AVALANCHE
            ),
        }

    def get_risk_history(
        self,
        location_id: str,
        hazard_type: HazardType | None = None,
        since: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[RiskAssessmentContract], int, bool]:
        """List historical assessments with pagination.

        Returns (items, total, has_next).
        """
        fetch_limit = page * page_size + 1
        all_items = self._risk_repo.list_history(
            location_id=location_id,
            hazard_type=hazard_type,
            since=since,
            limit=fetch_limit,
        )
        total_fetched = len(all_items)
        start_idx = (page - 1) * page_size
        page_items = all_items[start_idx : start_idx + page_size]
        has_next = total_fetched > page * page_size
        total = total_fetched if not has_next else total_fetched - 1
        return page_items, total, has_next

    def get_location_risk_state(self, location_id: str) -> LocationRiskState:
        """Get unified multi-hazard state without blending hazard engines."""
        flood = self._risk_repo.get_latest_for_location_and_hazard(
            location_id, HazardType.FLOOD
        )
        avalanche = self._risk_repo.get_latest_for_location_and_hazard(
            location_id, HazardType.AVALANCHE
        )
        if flood is None and avalanche is None:
            raise LocationNotFoundError(
                f"No risk assessments found for location '{location_id}'."
            )
        return self._orchestrator.get_location_risk_state(location_id)

    def get_replay_events(
        self,
        location_id: str | None = None,
        hazard_type: HazardType | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> ReplayEventsResponse:
        """Build chronological replay event sequences from persisted risk history.

        Groups persisted risk assessments by hazard pathway into replay events,
        with each assessment becoming a timestamped frame. Hazard pathways remain
        distinct and are never blended.
        """
        if location_id is not None:
            location = self._location_repo.get_by_id(location_id)
            if location is None:
                raise LocationNotFoundError(f"Location '{location_id}' not found.")
        else:
            location = None

        all_items = self._risk_repo.list_history(
            location_id=location_id,
            hazard_type=hazard_type,
            since=since,
            limit=limit,
        )

        # Reverse to chronological order (oldest first) for playback.
        all_items.reverse()

        # Group by (location_id, hazard_type) so each location gets its own
        # flood and avalanche events. Frames from different locations are
        # never mixed.
        by_location_and_hazard: dict[tuple[str | None, HazardType], list[RiskAssessmentContract]] = {}
        for item in all_items:
            key = (item.location_id, item.hazard_type)
            by_location_and_hazard.setdefault(key, []).append(item)

        events: list[ReplayEventContract] = []
        for (loc_id, ht), assessments in sorted(
            by_location_and_hazard.items(), key=lambda kv: (kv[0][0] or "", kv[0][1].value)
        ):
            if not assessments:
                continue

            location = None
            if loc_id is not None:
                location = self._location_repo.get_by_id(loc_id)
            location_display = loc_id or "all"
            sector_name = location.admin_unit if location else "All Locations"
            is_demo = location.is_demo_fixture if location else False

            event_id = f"replay-{location_display}-{ht.value}"
            title = f"{ht.value.title()} Risk History — {location_display}"
            date_range = (
                f"{assessments[0].assessed_at.strftime('%Y-%m-%d')} "
                f"to {assessments[-1].assessed_at.strftime('%Y-%m-%d')}"
            )

            frames: list[ReplayFrameContract] = []
            for idx, assessment in enumerate(assessments[:limit]):
                frames.append(
                    ReplayFrameContract(
                        id=f"{event_id}-f{idx}",
                        timestamp=assessment.assessed_at.isoformat(),
                        phase_label=(
                            f"T+{idx} • "
                            f"{assessment.assessed_at.strftime('%Y-%m-%d %H:%M UTC')}"
                        ),
                        primary_metric_label="Risk Score",
                        primary_metric_value=(
                            f"{(assessment.score or 0) * 100:.0f}%"
                            if assessment.score is not None
                            else "N/A"
                        ),
                        secondary_metric_label="Confidence",
                        secondary_metric_value=f"{assessment.confidence * 100:.0f}%",
                        alert_tier=_risk_class_to_alert_tier(assessment.risk_class),
                        risk_class=assessment.risk_class.value,
                        score=assessment.score,
                        confidence=assessment.confidence,
                        summary=(
                            f"{ht.value} risk assessed at {assessment.risk_class.value} "
                            f"level ({assessment.confidence * 100:.0f}% confidence)."
                        ),
                    )
                )

            events.append(
                ReplayEventContract(
                    id=event_id,
                    location_id=location_display,
                    title=title,
                    sector=sector_name,
                    hazard=ht.value,
                    date_range=date_range,
                    provenance="Persisted risk assessment history",
                    is_demo_fixture=is_demo,
                    frames=frames,
                )
            )

        return ReplayEventsResponse(total=len(events), items=events)


def _risk_class_to_alert_tier(risk_class: RiskClass) -> str:
    """Map a risk class to a human-readable alert tier for replay display."""
    return {
        RiskClass.SEVERE: "Emergency",
        RiskClass.HIGH: "High Risk",
        RiskClass.MODERATE: "Watch",
        RiskClass.LOW: "Normal",
        RiskClass.UNSUPPORTED: "Unknown",
    }[risk_class]
