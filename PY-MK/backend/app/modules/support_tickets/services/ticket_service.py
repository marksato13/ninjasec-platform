from __future__ import annotations

import json

from datetime import datetime

from app.core.time_utils import utcnow
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.device import Device
from app.db.models.integration import Integration
from app.db.models.client_system import ClientSystem
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.project_task import ProjectTask
from app.db.models.user import User
from app.db.models.enums import ProjectTaskStatus, RoleCode, TicketPriority, TicketStatus
from app.db.models.security_review import ReviewFinding, SecurityReview
from app.db.models.support_ticket import SupportTicket, SupportTicketEvent
from app.db.repositories.base import Repository
from app.modules.audit.services.audit_service import AuditService
from app.modules.support_tickets.schemas import (
    SupportTicketCreate,
    SupportTicketUpdate,
    TicketClientDecision,
    TicketConvert,
    TicketEstimate,
    TicketEventCreate,
    TicketFromFindingCreate,
    TicketStats,
)


class TicketService:
    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self._audit = AuditService(db)

    def _client_profile(self) -> ClientProfile | None:
        return self.db.scalar(
            select(ClientProfile).where(ClientProfile.user_id == self.current_user.id)
        )

    def _base_stmt(self):
        return select(SupportTicket).where(
            SupportTicket.organization_id == self.current_user.organization_id
        )

    def list(
        self,
        client_id: int | None = None,
        ticket_status: str | None = None,
        priority: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[SupportTicket]:
        stmt = self._base_stmt()
        if self.current_user.role == RoleCode.CLIENT.value:
            profile = self._client_profile()
            if not profile:
                return []
            stmt = stmt.where(SupportTicket.client_id == profile.client_id)
        elif client_id:
            stmt = stmt.where(SupportTicket.client_id == client_id)
        if ticket_status:
            stmt = stmt.where(SupportTicket.status == ticket_status)
        if priority:
            stmt = stmt.where(SupportTicket.priority == priority)
        if date_from:
            stmt = stmt.where(SupportTicket.opened_at >= date_from)
        if date_to:
            stmt = stmt.where(SupportTicket.opened_at <= date_to)
        stmt = stmt.order_by(SupportTicket.opened_at.desc())
        return list(self.db.scalars(stmt).all())

    def query_for_export(
        self,
        client_id: int | None = None,
        ticket_status: str | None = None,
        priority: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[SupportTicket]:
        stmt = self._base_stmt()
        if client_id:
            stmt = stmt.where(SupportTicket.client_id == client_id)
        if ticket_status:
            stmt = stmt.where(SupportTicket.status == ticket_status)
        if priority:
            stmt = stmt.where(SupportTicket.priority == priority)
        if date_from:
            stmt = stmt.where(SupportTicket.opened_at >= date_from)
        if date_to:
            stmt = stmt.where(SupportTicket.opened_at <= date_to)
        stmt = stmt.order_by(SupportTicket.opened_at.desc())
        return list(self.db.scalars(stmt).all())

    def stats(
        self,
        client_id: int | None = None,
        date_from: datetime | None = None,
    ) -> TicketStats:
        stmt = self._base_stmt()
        if client_id:
            stmt = stmt.where(SupportTicket.client_id == client_id)
        if date_from:
            stmt = stmt.where(SupportTicket.opened_at >= date_from)

        tickets = self.db.scalars(stmt).all()
        by_status: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        resolution_hours: list[float] = []

        for t in tickets:
            s = str(t.status)
            p = str(t.priority)
            by_status[s] = by_status.get(s, 0) + 1
            by_priority[p] = by_priority.get(p, 0) + 1
            if t.closed_at and t.opened_at:
                delta = (t.closed_at - t.opened_at).total_seconds() / 3600
                resolution_hours.append(delta)

        avg_hours = round(sum(resolution_hours) / len(resolution_hours), 2) if resolution_hours else None
        return TicketStats(
            total=len(tickets),
            by_status=by_status,
            by_priority=by_priority,
            open_count=by_status.get(TicketStatus.OPEN, 0) + by_status.get(TicketStatus.IN_PROGRESS, 0),
            closed_count=by_status.get(TicketStatus.CLOSED, 0),
            avg_resolution_hours=avg_hours,
        )

    def get_or_404(self, ticket_id: int) -> SupportTicket:
        stmt = (
            select(SupportTicket)
            .where(
                SupportTicket.id == ticket_id,
                SupportTicket.organization_id == self.current_user.organization_id,
            )
            .options(selectinload(SupportTicket.events))
        )
        ticket = self.db.scalar(stmt)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if self.current_user.role == RoleCode.CLIENT.value:
            profile = self._client_profile()
            if not profile or ticket.client_id != profile.client_id:
                raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket

    def _validar_sistema(self, system_id: int | None, client_id: int | None) -> None:
        """El sistema tiene que ser de esta organización y de este cliente: si no, 404."""
        if system_id is None:
            return
        sistema = self.db.get(ClientSystem, system_id)
        if (
            sistema is None
            or sistema.organization_id != self.current_user.organization_id
            or sistema.client_id != client_id
        ):
            raise HTTPException(status_code=404, detail="System not found")

    def _validar_cliente(self, client_id: int | None) -> None:
        """El cliente tiene que ser de esta organización: si no, 404."""
        cliente = self.db.get(Client, client_id) if client_id is not None else None
        if cliente is None or cliente.organization_id != self.current_user.organization_id:
            raise HTTPException(status_code=404, detail="Client not found")

    def _validar_responsable(self, user_id: int | None) -> None:
        """Solo se asigna a alguien del equipo de esta organización."""
        if user_id is None:
            return
        u = self.db.get(User, user_id)
        if u is None or u.organization_id != self.current_user.organization_id or u.role_code == RoleCode.CLIENT:
            raise HTTPException(status_code=404, detail="User not found")

    def _validar_referencias(self, payload: SupportTicketCreate) -> None:
        """Todo lo que el ticket enlaza tiene que ser de esta organización y de este cliente.

        Sin esto, alguien podía abrir un ticket contra el cliente, el equipo, la
        revisión o el hallazgo de otra organización, o un cliente enlazar los de otro.
        """
        org, cid = self.current_user.organization_id, payload.client_id
        self._validar_cliente(cid)
        if payload.integration_id is not None:
            integ = self.db.get(Integration, payload.integration_id)
            if integ is None or integ.organization_id != org or integ.client_id not in (None, cid):
                raise HTTPException(status_code=404, detail="Integration not found")
        if payload.device_id is not None:
            dev = self.db.get(Device, payload.device_id)
            integ = self.db.get(Integration, dev.integration_id) if dev and dev.integration_id else None
            if integ is None or integ.organization_id != org or integ.client_id not in (None, cid):
                raise HTTPException(status_code=404, detail="Device not found")
        if payload.review_id is not None:
            rev = self.db.get(SecurityReview, payload.review_id)
            if rev is None or rev.organization_id != org or rev.client_id != cid:
                raise HTTPException(status_code=404, detail="Review not found")
        if payload.finding_id is not None:
            hallazgo = self.db.get(ReviewFinding, payload.finding_id)
            rev = self.db.get(SecurityReview, hallazgo.review_id) if hallazgo else None
            if (rev is None or rev.organization_id != org or rev.client_id != cid
                    or (payload.review_id is not None and hallazgo.review_id != payload.review_id)):
                raise HTTPException(status_code=404, detail="Finding not found")
        self._validar_responsable(payload.assigned_to)
        self._validar_sistema(payload.system_id, cid)

    def create(self, payload: SupportTicketCreate) -> SupportTicket:
        self._validar_referencias(payload)
        ticket = SupportTicket(
            organization_id=self.current_user.organization_id,
            client_id=payload.client_id,
            integration_id=payload.integration_id,
            device_id=payload.device_id,
            review_id=payload.review_id,
            finding_id=payload.finding_id,
            title=payload.title,
            description=payload.description,
            category=payload.category,
            priority=TicketPriority(payload.priority),
            status=TicketStatus.OPEN,
            assigned_to=payload.assigned_to,
            kind=payload.kind,
            system_id=payload.system_id,
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        self._audit.record(
            self.current_user.organization_id,
            "support_ticket.created",
            "support_tickets",
            str(ticket.id),
            self.current_user.id,
            json.dumps({"kind": ticket.kind, "system_id": ticket.system_id}),
        )
        return ticket

    def create_from_finding(self, finding_id: int, payload: TicketFromFindingCreate) -> SupportTicket:
        finding = Repository(self.db).get_by_id(ReviewFinding, finding_id)
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")

        review = Repository(self.db).get_by_id(SecurityReview, finding.review_id)
        if not review or review.organization_id != self.current_user.organization_id:
            raise HTTPException(status_code=404, detail="Finding not found")

        ticket = SupportTicket(
            organization_id=self.current_user.organization_id,
            client_id=review.client_id,
            integration_id=review.integration_id,
            review_id=review.id,
            finding_id=finding.id,
            title=f"[{str(finding.severity).upper()}] {finding.title}",
            description=payload.description_override or finding.description,
            category=payload.category,
            priority=TicketPriority(payload.priority),
            status=TicketStatus.OPEN,
            assigned_to=payload.assigned_to,
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        self._audit.record(
            self.current_user.organization_id,
            "support_ticket.created_from_finding",
            "support_tickets",
            str(ticket.id),
            self.current_user.id,
        )
        return ticket

    def update(self, ticket_id: int, payload: SupportTicketUpdate) -> SupportTicket:
        ticket = Repository(self.db).get_by_id(SupportTicket, ticket_id)
        if not ticket or ticket.organization_id != self.current_user.organization_id:
            raise HTTPException(status_code=404, detail="Ticket not found")

        data = payload.model_dump(exclude_unset=True)
        if "assigned_to" in data:
            self._validar_responsable(data["assigned_to"])
        new_status = data.get("status") or str(ticket.status)

        if new_status == TicketStatus.CLOSED and not (data.get("resolution") or ticket.resolution):
            raise HTTPException(status_code=422, detail="resolution is required to close a ticket")

        prev_status = str(ticket.status)
        for field, value in data.items():
            if field == "status" and value is not None:
                value = TicketStatus(value)
            if field == "priority" and value is not None:
                value = TicketPriority(value)
            setattr(ticket, field, value)

        if new_status == TicketStatus.CLOSED and not ticket.closed_at:
            ticket.closed_at = utcnow()

        self.db.add(ticket)

        if "status" in data and prev_status != str(ticket.status):
            self.db.add(SupportTicketEvent(
                ticket_id=ticket.id,
                event_type="status_change",
                from_status=prev_status,
                to_status=str(ticket.status),
                user_id=self.current_user.id,
            ))

        self.db.commit()
        self.db.refresh(ticket)
        self._audit.record(
            self.current_user.organization_id,
            "support_ticket.updated",
            "support_tickets",
            str(ticket.id),
            self.current_user.id,
        )
        return ticket

    def delete(self, ticket_id: int) -> None:
        ticket = Repository(self.db).get_by_id(SupportTicket, ticket_id)
        if not ticket or ticket.organization_id != self.current_user.organization_id:
            raise HTTPException(status_code=404, detail="Ticket not found")
        self.db.delete(ticket)
        self.db.commit()
        self._audit.record(
            self.current_user.organization_id,
            "support_ticket.deleted",
            "support_tickets",
            str(ticket_id),
            self.current_user.id,
        )

    def add_event(self, ticket_id: int, payload: TicketEventCreate) -> SupportTicketEvent:
        ticket = Repository(self.db).get_by_id(SupportTicket, ticket_id)
        if not ticket or ticket.organization_id != self.current_user.organization_id:
            raise HTTPException(status_code=404, detail="Ticket not found")
        event = SupportTicketEvent(
            ticket_id=ticket_id,
            event_type=payload.event_type,
            user_id=self.current_user.id,
            notes=payload.notes,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    # ------------------------------------------------------------------
    # 35-P-03 · solicitudes de cambio: estimar → decide el cliente → tareas
    # ------------------------------------------------------------------

    def _cambio_o_404(self, ticket_id: int) -> SupportTicket:
        ticket = self.get_or_404(ticket_id)  # aplica organización y, si es cliente, su cliente
        if ticket.kind != "cambio":
            raise HTTPException(status_code=409, detail="Solo una solicitud de cambio se estima y se decide")
        return ticket

    def _evento(self, ticket: SupportTicket, tipo: str, notas: str | None = None) -> None:
        self.db.add(SupportTicketEvent(ticket_id=ticket.id, event_type=tipo, user_id=self.current_user.id,
                                       notes=notas))

    def estimate(self, ticket_id: int, payload: TicketEstimate) -> SupportTicket:
        ticket = self._cambio_o_404(ticket_id)
        if ticket.client_decision == "approved":
            raise HTTPException(status_code=409, detail="El cliente ya aprobó esta estimación")
        if ticket.converted_project_id is not None:
            raise HTTPException(status_code=409, detail="El cambio ya se convirtió en tareas")
        anterior = ticket.client_decision
        ticket.estimate_hours = payload.hours
        ticket.estimate_note = payload.note
        ticket.estimated_by = self.current_user.id
        ticket.estimated_at = utcnow()
        # Reestimar tras un rechazo abre una decisión nueva; la anterior queda en eventos y auditoría.
        ticket.client_decision = None
        ticket.client_decision_note = None
        ticket.client_decision_by = None
        ticket.client_decision_at = None
        self._evento(ticket, "change_estimated", f"{payload.hours} h")
        self.db.commit()
        self.db.refresh(ticket)
        self._audit.record(
            self.current_user.organization_id, "support_ticket.change_estimated", "support_tickets",
            str(ticket.id), self.current_user.id, json.dumps({"hours": payload.hours, "previous_decision": anterior}),
        )
        return ticket

    def decide(self, ticket_id: int, payload: TicketClientDecision) -> SupportTicket:
        if self.current_user.role != RoleCode.CLIENT.value:
            raise HTTPException(status_code=403, detail="Solo el cliente decide sobre su cambio")
        ticket = self._cambio_o_404(ticket_id)
        if ticket.estimate_hours is None:
            raise HTTPException(status_code=409, detail="El cambio aún no tiene estimación")
        if ticket.client_decision is not None:
            raise HTTPException(status_code=409, detail="Ya decidiste sobre esta estimación")
        nota = (payload.note or "").strip() or None
        if payload.decision == "rejected" and (nota is None or len(nota) < 5):
            raise HTTPException(status_code=422, detail="Cuéntanos por qué lo rechazas (mínimo 5 caracteres)")
        ticket.client_decision = payload.decision
        ticket.client_decision_note = nota
        ticket.client_decision_by = self.current_user.id
        ticket.client_decision_at = utcnow()
        self._evento(ticket, f"change_{payload.decision}", nota)
        self.db.commit()
        self.db.refresh(ticket)
        self._audit.record(
            self.current_user.organization_id, f"support_ticket.change_{payload.decision}", "support_tickets",
            str(ticket.id), self.current_user.id, json.dumps({"estimate_hours": float(ticket.estimate_hours)}),
        )
        return ticket

    def convert(self, ticket_id: int, payload: TicketConvert) -> SupportTicket:
        ticket = self._cambio_o_404(ticket_id)
        if ticket.client_decision != "approved":
            raise HTTPException(status_code=409, detail="El cliente aún no aprobó el cambio")
        if ticket.converted_project_id is not None:
            raise HTTPException(status_code=409, detail="El cambio ya se convirtió en tareas")
        org = self.current_user.organization_id

        responsable = self.db.get(User, payload.assigned_user_id)
        if (
            responsable is None
            or responsable.organization_id != org
            or responsable.role_code.value == RoleCode.CLIENT.value
        ):
            raise HTTPException(status_code=404, detail="User not found")

        if payload.project_id is not None:
            proyecto = self.db.get(Project, payload.project_id)
            if proyecto is None or proyecto.organization_id != org or proyecto.client_id != ticket.client_id:
                raise HTTPException(status_code=404, detail="Project not found")
            nuevo = False
        else:
            proyecto = Project(organization_id=org, client_id=ticket.client_id,
                               name=(payload.project_name or f"Cambio: {ticket.title}")[:160])
            self.db.add(proyecto)
            self.db.flush()
            nuevo = True

        descripcion = ticket.description or ""
        if ticket.estimate_hours is not None:
            descripcion = f"Ticket #{ticket.id} · {float(ticket.estimate_hours):g} h estimadas. {descripcion}"
        tarea = ProjectTask(organization_id=org, project_id=proyecto.id, assigned_user_id=responsable.id,
                            title=ticket.title[:160], description=descripcion.strip()[:500] or None,
                            status=ProjectTaskStatus.PENDING)
        self.db.add(tarea)
        ya_es_miembro = self.db.scalar(select(ProjectMember.id).where(
            ProjectMember.project_id == proyecto.id, ProjectMember.user_id == responsable.id))
        if ya_es_miembro is None:
            self.db.add(ProjectMember(project_id=proyecto.id, user_id=responsable.id))

        anterior = str(ticket.status)
        ticket.converted_project_id = proyecto.id
        ticket.status = TicketStatus.IN_PROGRESS
        self.db.add(SupportTicketEvent(ticket_id=ticket.id, event_type="change_converted",
                                       from_status=anterior, to_status=str(ticket.status),
                                       user_id=self.current_user.id, notes=f"proyecto {proyecto.id}"))
        self.db.commit()
        self.db.refresh(ticket)
        self._audit.record(
            org, "support_ticket.change_converted", "support_tickets", str(ticket.id), self.current_user.id,
            json.dumps({"project_id": proyecto.id, "new_project": nuevo, "task_id": tarea.id}),
        )
        return ticket
