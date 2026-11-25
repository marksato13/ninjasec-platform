from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.client import Client
from app.db.models.client_contact import ClientContact
from app.db.models.enums import ClientStatus, LeadStatus
from app.db.models.lead import Lead
from app.db.models.organization import Organization
from app.modules.audit.services.audit_service import AuditService
from app.modules.leads.schemas import LeadCreate, LeadInfoUpdate, LeadUpdate


class LeadService:
    def __init__(self, db: Session, current_user=None):
        self.db = db
        self.current_user = current_user

    def list(self) -> list[Lead]:
        stmt = select(Lead).where(Lead.organization_id == self.current_user.organization_id)
        return list(self.db.scalars(stmt).all())

    def _get_or_404(self, lead_id: int, *, for_update: bool = False) -> Lead:
        """404 tambien si el lead es de otra organizacion: no confirmar que existe."""
        stmt = select(Lead).where(
            Lead.id == lead_id, Lead.organization_id == self.current_user.organization_id
        )
        if for_update:
            stmt = stmt.with_for_update()
        lead = self.db.scalar(stmt)
        if lead is None:
            raise HTTPException(status_code=404, detail="Lead not found")
        return lead

    def _site_organization_id(self) -> int:
        """El formulario publico es del sitio, y el sitio es de la primera organizacion."""
        org_id = self.db.scalar(select(func.min(Organization.id)))
        if org_id is None:
            raise HTTPException(status_code=503, detail="El sitio aun no tiene organizacion")
        return org_id

    def create(self, payload: LeadCreate) -> Lead:
        lead = Lead(
            **{**payload.model_dump(), "status": LeadStatus.NEW},
            organization_id=self._site_organization_id(),
        )
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def update_info(self, lead_id: int, payload: LeadInfoUpdate) -> Lead:
        lead = self._get_or_404(lead_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(lead, field, value)
        self.db.commit()
        self.db.refresh(lead)
        if self.current_user:
            AuditService(self.db).record(
                self.current_user.organization_id,
                "lead.updated",
                "leads",
                str(lead.id),
                self.current_user.id,
            )
        return lead

    def delete(self, lead_id: int) -> None:
        lead = self._get_or_404(lead_id)
        self.db.delete(lead)
        self.db.commit()
        if self.current_user:
            AuditService(self.db).record(
                self.current_user.organization_id,
                "lead.deleted",
                "leads",
                str(lead_id),
                self.current_user.id,
            )

    def update_status(self, lead_id: int, payload: LeadUpdate) -> Lead:
        lead = self._get_or_404(lead_id)
        try:
            lead.status = LeadStatus(payload.status)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid status: {payload.status}")
        self.db.commit()
        self.db.refresh(lead)
        if self.current_user:
            AuditService(self.db).record(
                self.current_user.organization_id,
                "lead.status_updated",
                "leads",
                str(lead.id),
                self.current_user.id,
            )
        return lead

    def convert(self, lead_id: int) -> tuple[Lead, Client]:
        """Convierte el lead en cliente: cliente + contacto principal + lead ganado, todo o nada.

        Antes lo hacia el navegador en dos pasos y el lead no quedaba marcado, asi que pulsar
        dos veces creaba dos clientes. Aqui el lead se bloquea (`FOR UPDATE`) mientras se decide,
        y queda enlazado a su cliente: un segundo intento recibe 409 en vez de un duplicado.

        El lead es de la organizacion del administrador (si no, 404) y el cliente nace en ella.
        """
        lead = self._get_or_404(lead_id, for_update=True)
        if lead.converted_client_id is not None:
            raise HTTPException(status_code=409, detail="Este lead ya fue convertido en cliente")
        if lead.status == LeadStatus.CLOSED_LOST:
            raise HTTPException(status_code=409, detail="Un lead perdido no se convierte en cliente")

        notas = " · ".join(
            x for x in (
                f"Interés: {lead.interest_area}" if lead.interest_area else None,
                f"Origen: {lead.source}" if lead.source else None,
                lead.message,
            ) if x
        )
        client = Client(
            organization_id=self.current_user.organization_id,
            company_name=(lead.company_name or lead.contact_name)[:160],
            commercial_status=ClientStatus.ACTIVE,
            notes=notas[:255] or None,
        )
        self.db.add(client)
        self.db.flush()
        self.db.add(ClientContact(client_id=client.id, name=lead.contact_name, email=lead.email,
                                  phone=lead.phone, is_primary=True))
        lead.status = LeadStatus.CLOSED_WON
        lead.converted_client_id = client.id
        self.db.commit()
        self.db.refresh(lead)
        self.db.refresh(client)

        AuditService(self.db).record(
            self.current_user.organization_id, "lead.converted", "leads", str(lead.id), self.current_user.id,
            metadata_json=f'{{"client_id": {client.id}}}',
        )
        return lead, client
