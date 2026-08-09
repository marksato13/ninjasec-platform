from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.client import Client
from app.db.models.compliance import (
    ClientControlStatus,
    ComplianceControl,
    ComplianceFramework,
)
from app.db.models.user import User
from app.modules.audit.services.audit_service import AuditService
from app.modules.compliance.schemas import ControlStatusRead, ControlStatusUpdate, SoaSummary

FRAMEWORK_SLUG = "iso-27001-2022"


class ComplianceService:
    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self._audit = AuditService(db)

    def _client_or_404(self, client_id: int) -> Client:
        client = self.db.get(Client, client_id)
        if not client or client.organization_id != self.current_user.organization_id:
            raise HTTPException(status_code=404, detail="Client not found")
        return client

    def _framework(self) -> ComplianceFramework:
        framework = self.db.scalar(
            select(ComplianceFramework).where(ComplianceFramework.slug == FRAMEWORK_SLUG)
        )
        if not framework:
            raise HTTPException(status_code=500, detail="Compliance framework not seeded")
        return framework

    def _rows_for_client(
        self, client_id: int
    ) -> list[tuple[ComplianceControl, ClientControlStatus | None]]:
        framework = self._framework()
        controls = list(
            self.db.scalars(
                select(ComplianceControl)
                .where(ComplianceControl.framework_id == framework.id)
                .order_by(ComplianceControl.code)
            ).all()
        )
        statuses = {
            s.control_id: s
            for s in self.db.scalars(
                select(ClientControlStatus).where(
                    ClientControlStatus.client_id == client_id,
                    ClientControlStatus.control_id.in_([c.id for c in controls]),
                )
            ).all()
        }
        return [(c, statuses.get(c.id)) for c in controls]

    def _to_read(self, control: ComplianceControl, status: ClientControlStatus | None) -> ControlStatusRead:
        responsible_name = None
        if status and status.responsible_user_id:
            user = self.db.get(User, status.responsible_user_id)
            responsible_name = user.full_name if user else None
        return ControlStatusRead(
            control_id=control.id,
            code=control.code,
            parent_code=control.parent_code,
            category=control.category,
            title=control.title,
            applicability=status.applicability if status else "applicable",
            implementation_status=status.implementation_status if status else "not_implemented",
            maturity_level=status.maturity_level if status else 0,
            justification=status.justification if status else None,
            responsible_user_id=status.responsible_user_id if status else None,
            responsible_user_name=responsible_name,
            target_date=status.target_date if status else None,
            updated_at=status.updated_at if status else None,
        )

    def list_controls(self, client_id: int) -> list[ControlStatusRead]:
        self._client_or_404(client_id)
        return [self._to_read(c, s) for c, s in self._rows_for_client(client_id)]

    def soa_summary(self, client_id: int) -> SoaSummary:
        self._client_or_404(client_id)
        rows = self._rows_for_client(client_id)
        reads = [self._to_read(c, s) for c, s in rows]

        applicable = [r for r in reads if r.applicability != "not_applicable"]
        implemented = [r for r in applicable if r.implementation_status == "implemented"]
        percentage = (
            round(100 * len(implemented) / len(applicable), 1) if applicable else 0.0
        )

        return SoaSummary(
            client_id=client_id,
            framework="ISO/IEC 27001:2022",
            total_controls=len(reads),
            applicable_controls=len(applicable),
            implemented_controls=len(implemented),
            compliance_percentage=percentage,
            controls=reads,
        )

    def update_status(
        self, client_id: int, control_id: int, payload: ControlStatusUpdate
    ) -> ControlStatusRead:
        self._client_or_404(client_id)
        control = self.db.get(ComplianceControl, control_id)
        if not control:
            raise HTTPException(status_code=404, detail="Control not found")

        status = self.db.scalar(
            select(ClientControlStatus).where(
                ClientControlStatus.client_id == client_id,
                ClientControlStatus.control_id == control_id,
            )
        )

        data = payload.model_dump(exclude_unset=True)
        current_applicability = status.applicability if status else "applicable"
        current_justification = status.justification if status else None
        effective_applicability = data.get("applicability", current_applicability)
        effective_justification = data.get("justification", current_justification)
        if effective_applicability == "not_applicable" and not (
            effective_justification and effective_justification.strip()
        ):
            # Validar ANTES de tocar la sesión -- un HTTPException a mitad
            # de un add()/setattr() sin commit deja la sesión con un
            # objeto pendiente que rompe el siguiente request en la misma
            # sesión (relevante en tests, que reutilizan una sola sesión).
            raise HTTPException(
                status_code=422,
                detail="justification es obligatoria para declarar un control not_applicable",
            )

        if status is None:
            status = ClientControlStatus(client_id=client_id, control_id=control_id)
            self.db.add(status)
        for field, value in data.items():
            setattr(status, field, value)

        self.db.commit()
        self.db.refresh(status)
        self._audit.record(
            self.current_user.organization_id,
            "compliance.control.updated",
            "client_control_status",
            str(status.id),
            self.current_user.id,
            metadata_json=f'{{"client_id":{client_id},"control_code":"{control.code}"}}',
        )
        return self._to_read(control, status)
