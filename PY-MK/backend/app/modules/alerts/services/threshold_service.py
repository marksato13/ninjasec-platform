from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models.organization_alert_threshold import OrganizationAlertThreshold

DEFAULT_OVERDUE_DAYS = 7
DEFAULT_NO_REVIEW_DAYS = 30


@dataclass(frozen=True)
class AlertThresholdValues:
    overdue_days: int = DEFAULT_OVERDUE_DAYS
    no_review_days: int = DEFAULT_NO_REVIEW_DAYS


def get_alert_thresholds(db: Session, organization_id: int) -> AlertThresholdValues:
    configured = db.get(OrganizationAlertThreshold, organization_id)
    if configured is None:
        return AlertThresholdValues()
    return AlertThresholdValues(
        overdue_days=configured.overdue_days,
        no_review_days=configured.no_review_days,
    )
