from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkWindowStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class WorkWindowImpact(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def _a_utc_sin_zona(valor: datetime) -> datetime:
    """Las columnas son TIMESTAMP sin zona en UTC; una hora con zona se convierte."""
    if valor.tzinfo is not None:
        return valor.astimezone(UTC).replace(tzinfo=None)
    return valor


class WorkWindowCreate(BaseModel):
    project_id: int
    title: str = Field(min_length=3, max_length=160)
    change_description: str = Field(min_length=10, max_length=5000)
    systems_affected: str | None = Field(default=None, max_length=500)
    impact: WorkWindowImpact = WorkWindowImpact.MEDIUM
    rollback_plan: str = Field(min_length=10, max_length=5000)
    is_emergency: bool = False
    starts_at: datetime
    ends_at: datetime

    _utc = field_validator("starts_at", "ends_at")(_a_utc_sin_zona)


class WorkWindowDecision(BaseModel):
    approve: bool
    comment: str | None = Field(default=None, max_length=1000)


class WorkWindowStatusChange(BaseModel):
    status: WorkWindowStatus
    note: str | None = Field(default=None, max_length=1000)


class WorkWindowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    project_id: int
    requested_by_user_id: int | None = None
    title: str
    change_description: str
    systems_affected: str | None = None
    impact: str
    rollback_plan: str
    is_emergency: bool
    starts_at: datetime
    ends_at: datetime
    status: str
    client_decision_by_user_id: int | None = None
    client_decision_at: datetime | None = None
    client_comment: str | None = None
    execution_note: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
