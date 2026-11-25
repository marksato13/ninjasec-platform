from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from app.common.schemas.base import ORMModel


class ProjectDocRead(ORMModel):
    id: int
    project_id: int
    doc_type_id: int
    title: str
    summary: str | None = None
    github_url: str | None = None
    file_url: str | None = None
    file_name: str | None = None
    file_type: str | None = None
    file_size: int | None = None
    preview_md: str | None = None
    visibility: str
    status: str
    enabled: bool
    created_by: int | None = None
    updated_by: int | None = None
    verified_by: int | None = None
    verified_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    client_decision: str | None = None
    client_decision_note: str | None = None
    client_decision_by: int | None = None
    client_decision_at: datetime | None = None


class ProjectDocClientDecision(ORMModel):
    """El cliente aprueba el documento o pide cambios; pedir cambios exige el motivo."""

    decision: Literal["approved", "changes_requested"]
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _motivo_si_pide_cambios(self) -> "ProjectDocClientDecision":
        nota = (self.note or "").strip()
        if self.decision == "changes_requested" and len(nota) < 5:
            raise ValueError("Explica qué cambios necesitas (al menos 5 caracteres).")
        self.note = nota or None
        return self


class ProjectDocCreate(ORMModel):
    project_id: int
    doc_type_id: int
    title: str
    summary: str | None = None
    github_url: str | None = None
    preview_md: str | None = None
    visibility: str = "internal"
    status: str = "draft"
    enabled: bool = True


class ProjectDocUpdate(ORMModel):
    title: str | None = None
    summary: str | None = None
    github_url: str | None = None
    preview_md: str | None = None
    visibility: str | None = None
    status: str | None = None
    enabled: bool | None = None


class ProjectDocVerify(ORMModel):
    status: str | None = None
    enabled: bool | None = None


class ProjectDocToggle(ORMModel):
    enabled: bool
