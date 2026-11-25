from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time_utils import utcnow
from app.db.base import Base
from app.db.models.enums import TicketLinkEntity, TicketPriority, TicketStatus


# 35-P-03: un ticket es una incidencia (algo falla) o un cambio (algo nuevo
# sobre un sistema que el cliente ya tiene).
TIPOS_TICKET = ("incidencia", "cambio")
DECISIONES_CAMBIO = ("approved", "rejected")


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    __table_args__ = (
        CheckConstraint("kind IN ('incidencia', 'cambio')", name="kind"),
        CheckConstraint("estimate_hours IS NULL OR estimate_hours > 0", name="estimate_hours"),
        CheckConstraint(
            "client_decision IS NULL OR client_decision IN ('approved', 'rejected')",
            name="client_decision",
        ),
        Index("ix_support_tickets_client_status", "client_id", "status"),
        Index("ix_support_tickets_org_opened", "organization_id", "opened_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    integration_id: Mapped[int | None] = mapped_column(
        ForeignKey("integrations.id"), nullable=True
    )
    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id"), nullable=True
    )
    review_id: Mapped[int | None] = mapped_column(
        ForeignKey("security_reviews.id"), nullable=True
    )
    finding_id: Mapped[int | None] = mapped_column(
        ForeignKey("review_findings.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority_enum"), nullable=False
    )
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status_enum"), default=TicketStatus.OPEN
    )
    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 35-P-03 · solicitudes de cambio
    kind: Mapped[str] = mapped_column(
        String(12), nullable=False, default="incidencia", server_default="incidencia"
    )
    system_id: Mapped[int | None] = mapped_column(
        ForeignKey("client_systems.id", ondelete="SET NULL"), nullable=True, index=True
    )
    estimate_hours: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    estimate_note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    estimated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    estimated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    client_decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    client_decision_note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    client_decision_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    client_decision_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    converted_project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    organization = relationship("Organization")
    client = relationship("Client", back_populates="support_tickets")
    integration = relationship("Integration", back_populates="support_tickets")
    device = relationship("Device", back_populates="support_tickets")
    review = relationship("SecurityReview", back_populates="support_tickets")
    finding = relationship("ReviewFinding", back_populates="support_tickets")
    assignee = relationship("User", foreign_keys=[assigned_to])
    system = relationship("ClientSystem")

    @property
    def warranty_until(self) -> date | None:
        """Fecha de garantía si es una incidencia de un sistema aún en garantía."""
        if self.kind != "incidencia" or self.system is None or self.system.warranty_until is None:
            return None
        return self.system.warranty_until if self.system.warranty_until >= date.today() else None
    events = relationship(
        "SupportTicketEvent", back_populates="ticket", cascade="all, delete-orphan"
    )
    links = relationship(
        "TicketLink", back_populates="ticket", cascade="all, delete-orphan"
    )


class SupportTicketEvent(Base):
    __tablename__ = "support_ticket_events"

    __table_args__ = (Index("ix_ticket_events_ticket", "ticket_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("support_tickets.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    ticket = relationship("SupportTicket", back_populates="events")
    user = relationship("User", foreign_keys=[user_id])


class TicketLink(Base):
    __tablename__ = "ticket_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("support_tickets.id"), nullable=False
    )
    entity_type: Mapped[TicketLinkEntity] = mapped_column(
        Enum(TicketLinkEntity, name="ticket_link_entity_enum"), nullable=False
    )
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)

    ticket = relationship("SupportTicket", back_populates="links")
