"""SQLAlchemy ORM model registry."""

from app.models.alert import AlertActionModel
from app.models.location import LocationModel
from app.models.observation import ObservationModel
from app.models.official_warning import OfficialWarningModel
from app.models.risk_assessment import RiskAssessmentModel
from app.models.source import SourceModel
from app.models.user import UserModel

__all__ = [
    "AlertActionModel",
    "LocationModel",
    "ObservationModel",
    "OfficialWarningModel",
    "RiskAssessmentModel",
    "SourceModel",
    "UserModel",
]
