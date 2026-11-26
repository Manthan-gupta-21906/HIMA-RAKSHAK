"""Controlled observation-to-risk assessment, exposure, priority, and alert workflow."""

from datetime import UTC, datetime
from functools import lru_cache

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.features.avalanche import extract_avalanche_features
from app.features.flood import FloodFeatureVector, extract_flood_features
from app.features.metadata import TerrainContext
from app.flood.model import FloodBaselineClassifier
from app.models.location import LocationRecord
from app.models.observation import ObservationModel
from app.repositories.alert_repository import AlertRepository
from app.repositories.gis_layer_repository import GisLayerRepository
from app.repositories.location_repository import SqlAlchemyLocationRepository
from app.repositories.observation_repository import ObservationRepository
from app.repositories.risk_repository import RiskAssessmentRepository
from app.risk.priority import calculate_priority_assessment
from app.schemas.alert import AlertActionRecord
from app.schemas.common import HazardType, ProvenanceMeta
from app.schemas.exposure import LocationExposureProfile, PriorityAssessment
from app.schemas.observation import ObservationContract, ObservationMetric
from app.schemas.risk import LocationRiskState, RiskAssessmentContract
from app.services.alert_service import AlertService
from app.services.exposure_service import SpatialExposureService
from app.services.location_service import LocationNotFoundError
from app.services.risk_orchestrator import RiskOrchestrator

PILOT_TERRAIN_CONTEXT: dict[str, TerrainContext] = {
    "JK-SGR-01": TerrainContext(
        elevation_m=1585.0, slope_deg=4.0, aspect_deg=180.0, drainage_density=1.8
    ),
    "JK-GUL-01": TerrainContext(
        elevation_m=3980.0, slope_deg=38.0, aspect_deg=45.0, drainage_density=0.9
    ),
    "JK-BAN-01": TerrainContext(
        elevation_m=1666.0, slope_deg=32.0, aspect_deg=135.0, drainage_density=1.5
    ),
    "JK-DRS-01": TerrainContext(
        elevation_m=3528.0, slope_deg=40.0, aspect_deg=315.0, drainage_density=0.7
    ),
}


@lru_cache(maxsize=1)
def get_pilot_flood_model() -> FloodBaselineClassifier:
    """Return a deterministic pilot-calibrated flood baseline classifier."""
    model = FloodBaselineClassifier(epochs=150, version="flood-baseline-v1")
    # Reproducible pilot calibration samples:
    # [rain_1h, rain_24h, antecedent_72h, river_level, river_rate, drainage_density]
    samples = [
        [2.0, 8.0, 12.0, 1.8, 0.02, 1.0],
        [5.0, 15.0, 20.0, 2.4, 0.05, 1.2],
        [8.0, 24.0, 30.0, 3.0, 0.08, 1.3],
        [25.0, 55.0, 60.0, 4.6, 0.25, 1.6],
        [40.0, 85.0, 90.0, 5.4, 0.45, 1.8],
        [55.0, 120.0, 110.0, 6.2, 0.65, 2.0],
    ]
    labels = [0, 0, 0, 1, 1, 1]
    feature_names = [
        "rain_1h_mm",
        "rain_24h_mm",
        "antecedent_rain_72h_mm",
        "river_level_m",
        "river_level_rate_m_per_h",
        "drainage_density",
    ]
    model.fit(samples, labels, feature_names=feature_names)
    return model


class RiskEvaluationResponse(BaseModel):
    """Unified result of the observation -> risk -> exposure -> priority -> alert workflow."""

    location_id: str
    risk_state: LocationRiskState
    exposure: LocationExposureProfile
    priority: PriorityAssessment
    alert: AlertActionRecord | None = None


class RiskWorkflowService:
    """Executes the full controlled hazard evaluation pipeline from persisted observations."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._loc_repo = SqlAlchemyLocationRepository(db)
        self._obs_repo = ObservationRepository(db)
        self._risk_repo = RiskAssessmentRepository(db)
        self._orchestrator = RiskOrchestrator(self._risk_repo)
        self._exposure_service = SpatialExposureService(
            layer_repo=GisLayerRepository(db)
        )
        self._alert_service = AlertService(AlertRepository(db))

    @staticmethod
    def _to_obs_contract(row: ObservationModel) -> ObservationContract:
        obs_at = row.observed_at
        if obs_at.tzinfo is None:
            obs_at = obs_at.replace(tzinfo=UTC)
        return ObservationContract(
            observation_id=row.observation_id,
            location_id=row.location_id,
            source_id=row.source_id,
            observed_at=obs_at,
            metric=ObservationMetric(row.metric),
            value=row.value,
            unit=row.unit,
            is_demo_fixture=row.is_demo_fixture,
        )

    def _get_location(self, location_id: str) -> LocationRecord:
        loc = self._loc_repo.get_by_id(location_id)
        if loc is None:
            raise LocationNotFoundError(f"Location '{location_id}' not found.")
        return loc

    @staticmethod
    def _has_flood_inputs(features: FloodFeatureVector) -> bool:
        return any(
            fv.value is not None
            for fv in (
                features.rain_1h_mm,
                features.rain_24h_mm,
                features.antecedent_rain_72h_mm,
                features.river_level_m,
            )
        )

    @staticmethod
    def _select_primary_assessment(state: LocationRiskState) -> RiskAssessmentContract | None:
        if state.primary_hazard == HazardType.FLOOD and state.flood is not None:
            return state.flood
        if state.primary_hazard == HazardType.AVALANCHE and state.avalanche is not None:
            return state.avalanche
        return state.flood or state.avalanche

    def evaluate_location(
        self,
        location_id: str,
        *,
        trigger_alert: bool = True,
    ) -> RiskEvaluationResponse:
        """Extract features from observations, run hazard pathways, and compute priority."""
        location = self._get_location(location_id)
        obs_rows = self._obs_repo.list_by_location(location_id)
        observations = [self._to_obs_contract(r) for r in obs_rows]
        cutoff_at = datetime.now(UTC)
        terrain = PILOT_TERRAIN_CONTEXT.get(location_id, TerrainContext())

        supported = {
            h.value if hasattr(h, "value") else str(h)
            for h in location.supported_hazards
        }
        has_flood_obs = any(
            o.metric in {ObservationMetric.RAIN_MM, ObservationMetric.RIVER_LEVEL_M}
            for o in observations
        )
        has_avalanche_obs = any(
            o.metric in {ObservationMetric.SNOW_DEPTH_CM, ObservationMetric.WIND_KMH}
            for o in observations
        )

        # 1. Flood pathway (kept strictly independent)
        if "flood" in supported or has_flood_obs:
            flood_features = extract_flood_features(
                location_id=location_id,
                observations=observations,
                cutoff_at=cutoff_at,
                terrain=terrain,
            )
            flood_model = (
                get_pilot_flood_model() if self._has_flood_inputs(flood_features) else None
            )
            self._orchestrator.assess_flood(
                flood_features,
                model=flood_model,
                source_meta=ProvenanceMeta(
                    source_id="src-cwc-01",
                    source_name="Central Water Commission & Field Telemetry",
                    licence="Government Open Data Licence - India (GODL)",
                    is_demo_fixture=False,
                    ingested_at=cutoff_at,
                ),
            )

        # 2. Avalanche pathway (kept strictly independent; readiness-gated)
        if "avalanche" in supported or has_avalanche_obs or not supported:
            avalanche_features = extract_avalanche_features(
                location_id=location_id,
                observations=observations,
                cutoff_at=cutoff_at,
                terrain=terrain,
            )
            self._orchestrator.assess_avalanche(
                avalanche_features,
                source_meta=ProvenanceMeta(
                    source_id="src-dgre-01",
                    source_name="DGRE Snowpack & Field Telemetry",
                    licence="Government Open Data Licence - India (GODL)",
                    is_demo_fixture=False,
                    ingested_at=cutoff_at,
                ),
            )

        risk_state = self._orchestrator.get_location_risk_state(location_id)
        primary_assessment = self._select_primary_assessment(risk_state)
        assert primary_assessment is not None

        exposure = self._exposure_service.calculate_exposure(location, primary_assessment)
        priority = calculate_priority_assessment(primary_assessment, exposure)
        alert = (
            self._alert_service.generate_for_assessment(primary_assessment, priority)
            if trigger_alert
            else None
        )

        return RiskEvaluationResponse(
            location_id=location_id,
            risk_state=risk_state,
            exposure=exposure,
            priority=priority,
            alert=alert,
        )

    def get_exposure(self, location_id: str) -> LocationExposureProfile:
        """Compute spatial exposure for a location using its latest primary hazard assessment."""
        location = self._get_location(location_id)
        risk_state = self._orchestrator.get_location_risk_state(location_id)
        primary = self._select_primary_assessment(risk_state)
        return self._exposure_service.calculate_exposure(location, primary)

    def get_priority(self, location_id: str) -> PriorityAssessment:
        """Compute explainable priority for a location from its latest hazard and exposure."""
        location = self._get_location(location_id)
        risk_state = self._orchestrator.get_location_risk_state(location_id)
        primary = self._select_primary_assessment(risk_state)
        if primary is None:
            raise LocationNotFoundError(
                f"No risk assessments found for location '{location_id}'."
            )
        exposure = self._exposure_service.calculate_exposure(location, primary)
        return calculate_priority_assessment(primary, exposure)
