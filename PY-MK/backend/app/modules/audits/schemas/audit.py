from datetime import date, datetime

from pydantic import field_validator

from app.common.schemas.base import ORMModel

VALID_FRAMEWORKS = {"cobit_2019", "iso_27001", "iso_19011", "custom"}
VALID_AUDIT_TYPES = {"internal", "external", "certification", "follow_up"}
VALID_STATUSES = {"planned", "in_progress", "reporting", "closed"}
VALID_OPINIONS = {"satisfactory", "with_observations", "unsatisfactory"}


class AuditRead(ORMModel):
    id: int
    organization_id: int
    client_id: int
    client_name: str | None = None
    code: str
    title: str
    objective: str | None = None
    scope: str | None = None
    framework: str
    audit_type: str
    lead_auditor_id: int
    lead_auditor_name: str | None = None
    planned_start: date | None = None
    planned_end: date | None = None
    actual_end: date | None = None
    status: str
    opinion: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AuditCreate(ORMModel):
    client_id: int
    title: str
    objective: str | None = None
    scope: str | None = None
    framework: str
    audit_type: str
    lead_auditor_id: int
    planned_start: date | None = None
    planned_end: date | None = None

    @field_validator("framework")
    @classmethod
    def _valid_framework(cls, value: str) -> str:
        if value not in VALID_FRAMEWORKS:
            raise ValueError(f"framework debe ser uno de {sorted(VALID_FRAMEWORKS)}")
        return value

    @field_validator("audit_type")
    @classmethod
    def _valid_audit_type(cls, value: str) -> str:
        if value not in VALID_AUDIT_TYPES:
            raise ValueError(f"audit_type debe ser uno de {sorted(VALID_AUDIT_TYPES)}")
        return value


class AuditUpdate(ORMModel):
    title: str | None = None
    objective: str | None = None
    scope: str | None = None
    lead_auditor_id: int | None = None
    planned_start: date | None = None
    planned_end: date | None = None
    actual_end: date | None = None
    status: str | None = None
    opinion: str | None = None

    @field_validator("status")
    @classmethod
    def _valid_status(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_STATUSES:
            raise ValueError(f"status debe ser uno de {sorted(VALID_STATUSES)}")
        return value

    @field_validator("opinion")
    @classmethod
    def _valid_opinion(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_OPINIONS:
            raise ValueError(f"opinion debe ser uno de {sorted(VALID_OPINIONS)}")
        return value
