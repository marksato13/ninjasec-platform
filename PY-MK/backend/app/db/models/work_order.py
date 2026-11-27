"""Órdenes de trabajo: solicitud → cotización → orden (planificación 36).

Toda tabla lleva ``organization_id``. El aislamiento entre organizaciones lo
hace el servicio y lo demuestran las pruebas de acceso (decisión en #119): la
plataforma no usa claves foráneas compuestas.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time_utils import utcnow
from app.db.base import Base
from app.modules.work_orders.services.states import (
    QUOTE_STATUSES,
    REQUEST_STATUSES,
    WORK_ORDER_STATUSES,
)

QUOTE_ITEM_KINDS = ("labor", "material", "travel")
PRIORITIES = ("low", "medium", "high", "critical")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class WorkRequest(Base):
    """Lo que pide el cliente, desde el portal o registrado por un admin."""

    __tablename__ = "work_requests"
    __table_args__ = (
        CheckConstraint(_in("status", REQUEST_STATUSES), name="status"),
        CheckConstraint(_in("priority", PRIORITIES), name="priority"),
        Index("ix_work_requests_org_status", "organization_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    site_id: Mapped[int | None] = mapped_column(
        ForeignKey("client_sites.id", ondelete="SET NULL"), nullable=True
    )
    requested_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    quotes = relationship("Quote", back_populates="request", order_by="Quote.version")


class Quote(Base):
    """Una versión de la cotización de una solicitud. Aprobada, no cambia (R-04)."""

    __tablename__ = "quotes"
    __table_args__ = (
        CheckConstraint(_in("status", QUOTE_STATUSES), name="status"),
        CheckConstraint("version >= 1", name="version"),
        CheckConstraint("subtotal >= 0 AND tax >= 0", name="amounts"),
        CheckConstraint("total = subtotal + tax", name="total"),
        UniqueConstraint("request_id", "version", name="uq_quotes_request_version"),
        # Como mucho una cotización viva (borrador o enviada) por solicitud.
        Index(
            "uq_quotes_request_open",
            "request_id",
            unique=True,
            postgresql_where=text("status IN ('draft', 'sent')"),
            sqlite_where=text("status IN ('draft', 'sent')"),
        ),
        Index("ix_quotes_org_status", "organization_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("work_requests.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    request = relationship("WorkRequest", back_populates="quotes")
    items = relationship(
        "QuoteItem", back_populates="quote", cascade="all, delete-orphan", order_by="QuoteItem.id"
    )
    work_order = relationship("WorkOrder", back_populates="quote", uselist=False)


class QuoteItem(Base):
    __tablename__ = "quote_items"
    __table_args__ = (
        CheckConstraint(_in("kind", QUOTE_ITEM_KINDS), name="kind"),
        CheckConstraint("quantity > 0", name="quantity"),
        CheckConstraint("unit_price >= 0", name="unit_price"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    quote_id: Mapped[int] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(12), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    quote = relationship("Quote", back_populates="items")


class WorkOrder(Base):
    """Nace sola al aprobarse una cotización: una por cotización (R-06)."""

    __tablename__ = "work_orders"
    __table_args__ = (
        CheckConstraint(_in("status", WORK_ORDER_STATUSES), name="status"),
        CheckConstraint(
            "assigned_to IS NOT NULL OR status IN ('pending_assignment', 'cancelled')",
            name="assignee",
        ),
        UniqueConstraint("organization_id", "number", name="uq_work_orders_org_number"),
        # R-01: «mis órdenes» del técnico.
        Index("ix_work_orders_org_assignee", "organization_id", "assigned_to", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id"), nullable=False, unique=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    site_id: Mapped[int | None] = mapped_column(
        ForeignKey("client_sites.id", ondelete="SET NULL"), nullable=True
    )
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending_assignment")
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completion_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    quote = relationship("Quote", back_populates="work_order")
    assignee = relationship("User", foreign_keys=[assigned_to])


class WorkEvent(Base):
    """Historial de estados de las tres entidades (R-10). Uno, y solo uno, de
    ``request_id``, ``quote_id`` o ``work_order_id`` va lleno."""

    __tablename__ = "work_events"
    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN request_id IS NULL THEN 0 ELSE 1 END)"
            " + (CASE WHEN quote_id IS NULL THEN 0 ELSE 1 END)"
            " + (CASE WHEN work_order_id IS NULL THEN 0 ELSE 1 END) = 1",
            name="one_entity",
        ),
        Index("ix_work_events_request", "request_id"),
        Index("ix_work_events_quote", "quote_id"),
        Index("ix_work_events_work_order", "work_order_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    request_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_requests.id", ondelete="CASCADE"), nullable=True
    )
    quote_id: Mapped[int | None] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"), nullable=True
    )
    work_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=True
    )
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # Nota interna: el cliente no la ve.
    internal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
