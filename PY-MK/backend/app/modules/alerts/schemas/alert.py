from datetime import datetime

from pydantic import BaseModel, Field


class AlertItem(BaseModel):
    type: str           # "license_expired" | "critical_finding_open" | "critical_device_offline" | "ticket_overdue"
    severity: str       # "critical" | "warning" | "info"
    entity_type: str    # "integration" | "review_finding" | "device" | "support_ticket"
    entity_id: int
    message: str
    created_at: datetime


class AlertRefreshResult(BaseModel):
    integrations_marked_risk: int
    devices_marked_pending_review: int


class AlertThresholds(BaseModel):
    overdue_days: int
    no_review_days: int


class AlertThresholdsUpdate(BaseModel):
    overdue_days: int = Field(ge=1, le=3650)
    no_review_days: int = Field(ge=1, le=3650)
