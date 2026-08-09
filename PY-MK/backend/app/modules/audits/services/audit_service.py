from __future__ import annotations

from datetime import date

from fastapi import HTTPException
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.db.models.audit import Audit
from app.db.models.client import Client
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.user import User
from app.db.repositories.base import Repository
from app.modules.audit.services.audit_service import AuditService as AuditLogService
from app.modules.audits.schemas import AuditCreate, AuditRead, AuditUpdate


class AuditManagementService:
    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self._audit_log = AuditLogService(db)

    def _client_or_404(self, client_id: int) -> Client:
        client = self.db.get(Client, client_id)
        if not client or client.organization_id != self.current_user.organization_id:
            raise HTTPException(status_code=404, detail="Client not found")
        return client

    def _is_operationally_responsible(self, user_id: int, client_id: int) -> bool:
        """26-P1: regla de independencia (ISO 19011) -- un auditor no puede
        auditar un cliente donde figura como responsable operativo. Se
        deriva de la membresía en proyectos activos de ese cliente: es la
        señal ya existente de "quién trabaja operativamente con este
        cliente" (no hay un campo dedicado 'responsable' en Client)."""
        member = self.db.scalar(
            select(ProjectMember)
            .join(Project, ProjectMember.project_id == Project.id)
            .where(Project.client_id == client_id, ProjectMember.user_id == user_id)
        )
        return member is not None

    def _next_code(self) -> str:
        year = date.today().year
        prefix = f"AUD-{year}-"
        count = self.db.scalar(
            select(func.count()).select_from(Audit).where(
                Audit.organization_id == self.current_user.organization_id,
                extract("year", Audit.created_at) == year,
            )
        ) or 0
        return f"{prefix}{count + 1:03d}"

    def _to_read(self, audit: Audit) -> AuditRead:
        client = self.db.get(Client, audit.client_id)
        auditor = self.db.get(User, audit.lead_auditor_id)
        return AuditRead(
            id=audit.id,
            organization_id=audit.organization_id,
            client_id=audit.client_id,
            client_name=client.company_name if client else None,
            code=audit.code,
            title=audit.title,
            objective=audit.objective,
            scope=audit.scope,
            framework=audit.framework,
            audit_type=audit.audit_type,
            lead_auditor_id=audit.lead_auditor_id,
            lead_auditor_name=auditor.full_name if auditor else None,
            planned_start=audit.planned_start,
            planned_end=audit.planned_end,
            actual_end=audit.actual_end,
            status=audit.status,
            opinion=audit.opinion,
            created_at=audit.created_at,
            updated_at=audit.updated_at,
        )

    def list(self, client_id: int | None = None) -> list[AuditRead]:
        stmt = select(Audit).where(Audit.organization_id == self.current_user.organization_id)
        if client_id:
            stmt = stmt.where(Audit.client_id == client_id)
        stmt = stmt.order_by(Audit.code.desc())
        return [self._to_read(a) for a in self.db.scalars(stmt).all()]

    def get(self, audit_id: int) -> Audit:
        audit = Repository(self.db).get_by_id(Audit, audit_id)
        if not audit or audit.organization_id != self.current_user.organization_id:
            raise HTTPException(status_code=404, detail="Audit not found")
        return audit

    def create(self, payload: AuditCreate) -> AuditRead:
        self._client_or_404(payload.client_id)

        auditor = self.db.get(User, payload.lead_auditor_id)
        if not auditor or auditor.organization_id != self.current_user.organization_id:
            raise HTTPException(status_code=404, detail="Lead auditor not found")

        if self._is_operationally_responsible(payload.lead_auditor_id, payload.client_id):
            raise HTTPException(
                status_code=422,
                detail=(
                    "El auditor líder no puede ser responsable operativo del cliente "
                    "auditado (regla de independencia, ISO 19011)"
                ),
            )

        audit = Audit(
            organization_id=self.current_user.organization_id,
            client_id=payload.client_id,
            code=self._next_code(),
            title=payload.title,
            objective=payload.objective,
            scope=payload.scope,
            framework=payload.framework,
            audit_type=payload.audit_type,
            lead_auditor_id=payload.lead_auditor_id,
            planned_start=payload.planned_start,
            planned_end=payload.planned_end,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        self._audit_log.record(
            self.current_user.organization_id,
            "audit.created",
            "audits",
            str(audit.id),
            self.current_user.id,
            metadata_json=f'{{"code":"{audit.code}","client_id":{audit.client_id}}}',
        )
        return self._to_read(audit)

    def update(self, audit_id: int, payload: AuditUpdate) -> AuditRead:
        audit = self.get(audit_id)

        data = payload.model_dump(exclude_unset=True)
        if "lead_auditor_id" in data and data["lead_auditor_id"] is not None:
            new_auditor_id = data["lead_auditor_id"]
            auditor = self.db.get(User, new_auditor_id)
            if not auditor or auditor.organization_id != self.current_user.organization_id:
                raise HTTPException(status_code=404, detail="Lead auditor not found")
            if self._is_operationally_responsible(new_auditor_id, audit.client_id):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "El auditor líder no puede ser responsable operativo del cliente "
                        "auditado (regla de independencia, ISO 19011)"
                    ),
                )

        for field, value in data.items():
            setattr(audit, field, value)

        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        self._audit_log.record(
            self.current_user.organization_id,
            "audit.updated",
            "audits",
            str(audit.id),
            self.current_user.id,
        )
        return self._to_read(audit)
