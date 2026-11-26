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
    HistoricalReplayEvent,
    LocationRiskState,
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

    @staticmethod
    def _risk_class_to_alert_tier(risk_class: RiskClass) -> str:
        return {
            RiskClass.LOW: "Watch",
            RiskClass.MODERATE: "Moderate",
            RiskClass.HIGH: "High Risk",
            RiskClass.SEVERE: "Emergency",
            RiskClass.UNSUPPORTED: "Unsupported",
        }.get(risk_class, "Watch")

    @staticmethod
    def _nearest_observation_metrics(
        hazard_type: HazardType,
        assessed_at: datetime,
        observations: list[object],
    ) -> tuple[str, str, str, str] | None:
        if not observations:
            return None
        preferred_metrics = (
            ("river_level", "rainfall_24h", "rainfall_1h")
            if hazard_type == HazardType.FLOOD
            else ("snowfall_24h", "snow_depth", "wind_speed", "temperature")
        )
        # Find observations within 24h of assessed_at, preferring hazard-relevant metrics.
        window_obs = [
            obs
            for obs in observations
            if abs((obs.observed_at - assessed_at).total_seconds()) <= 86400  # type: ignore[attr-defined]
        ]
        if not window_obs:
            return None

        by_metric: dict[str, object] = {}
        for obs in sorted(
            window_obs,
            key=lambda o: abs((o.observed_at - assessed_at).total_seconds()),  # type: ignore[attr-defined]
        ):
            m_val = obs.metric.value if hasattr(obs.metric, "value") else str(obs.metric)  # type: ignore[attr-defined]
            if m_val not in by_metric:
                by_metric[m_val] = obs

        chosen = [by_metric[m] for m in preferred_metrics if m in by_metric]
        if not chosen:
            chosen = list(by_metric.values())[:2]

        def _fmt(obs: object) -> tuple[str, str]:
            m_val = obs.metric.value if hasattr(obs.metric, "value") else str(obs.metric)  # type: ignore[attr-defined]
            label = m_val.replace("_", " ").title()
            val = f"{obs.value:g} {obs.unit}".strip()  # type: ignore[attr-defined]
            return label, val

        p_label, p_val = _fmt(chosen[0])
        if len(chosen) > 1:
            s_label, s_val = _fmt(chosen[1])
            return p_label, p_val, s_label, s_val
        return p_label, p_val, "", ""

    def get_replay_events(
        self,
        location_id: str | None = None,
        hazard_type: HazardType | None = None,
        since: datetime | None = None,
        limit_per_location: int = 50,
    ) -> list[HistoricalReplayEvent]:
        """Reconstruct chronological replay sequences.

        Uses persisted risk and observation history.
        """
        if location_id is not None:
            loc = self._location_repo.get_by_id(location_id)
            if loc is None:
                raise LocationNotFoundError(f"Location '{location_id}' not found.")
            locations = [loc]
        else:
            locations = self._location_repo.list_all()

        events: list[HistoricalReplayEvent] = []
        for loc in locations:
            history = self._risk_repo.list_history(
                location_id=loc.location_id,
                hazard_type=hazard_type,
                since=since,
                limit=limit_per_location,
            )
            if not history:
                continue

            obs_models = self._observation_repo.list_by_location(loc.location_id)
            obs_contracts = [model_to_contract(m) for m in obs_models]

            grouped: dict[HazardType, list[RiskAssessmentContract]] = {}
            for item in history:
                grouped.setdefault(item.hazard_type, []).append(item)

            for hz, items in grouped.items():
                ordered = sorted(items, key=lambda r: r.assessed_at)
                start_ts = ordered[0].assessed_at
                end_ts = ordered[-1].assessed_at
                frames: list[ReplayFrameContract] = []

                for idx, item in enumerate(ordered):
                    elapsed_h = int(
                        max(0.0, (item.assessed_at - start_ts).total_seconds() // 3600)
                    )
                    tier = self._risk_class_to_alert_tier(item.risk_class)
                    if idx == 0:
                        stage = "Initial"
                    elif item.risk_class in {RiskClass.HIGH, RiskClass.SEVERE}:
                        stage = "Peak / Escalation"
                    elif idx == len(ordered) - 1:
                        stage = "Latest"
                    else:
                        stage = "Progression"

                    obs_metrics = self._nearest_observation_metrics(
                        hz, item.assessed_at, obs_contracts
                    )
                    score_str = (
                        f"{round(item.score * 100)}%"
                        if item.score is not None
                        else "Unsupported"
                    )
                    conf_str = f"{round(item.confidence * 100)}%"

                    if obs_metrics and obs_metrics[2]:
                        p_label, p_val, s_label, s_val = obs_metrics
                    elif obs_metrics:
                        p_label, p_val = obs_metrics[0], obs_metrics[1]
                        s_label, s_val = "Hazard Score", score_str
                    else:
                        p_label, p_val = "Hazard Score", score_str
                        s_label, s_val = "Confidence", conf_str

                    summary = item.readiness_reason or (
                        f"{hz.value.title()} assessment: {item.risk_class.value} "
                        f"({item.prediction_status.value}, confidence {conf_str}, "
                        f"source {item.provenance.source_name})."
                    )
                    frames.append(
                        ReplayFrameContract(
                            id=item.risk_id,
                            timestamp=item.assessed_at,
                            phase_label=f"T+{elapsed_h:02d}h • {stage}",
                            primary_metric_label=p_label,
                            primary_metric_value=p_val,
                            secondary_metric_label=s_label,
                            secondary_metric_value=s_val,
                            alert_tier=tier,
                            risk_class=item.risk_class,
                            score=item.score,
                            confidence=item.confidence,
                            summary=summary,
                        )
                    )

                latest_prov = ordered[-1].provenance
                events.append(
                    HistoricalReplayEvent(
                        id=f"HIST-{loc.location_id}-{hz.value.upper()}",
                        location_id=loc.location_id,
                        title=f"{loc.name} — {hz.value.title()} History",
                        sector=f"{loc.name} ({loc.location_id})",
                        hazard=hz,
                        date_range=f"{start_ts.date().isoformat()} to {end_ts.date().isoformat()}",
                        provenance=f"Persisted History ({latest_prov.source_name})",
                        is_demo_fixture=any(r.provenance.is_demo_fixture for r in ordered),
                        frames=frames,
                    )
                )

        return events
