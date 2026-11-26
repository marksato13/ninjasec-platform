from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time_utils import utcnow
from app.db.base import Base


class PaymentMilestone(Base):
    """Un hito de pago de un proyecto (C3).

    Solo registra el estado: no hay pasarela, ni datos bancarios, ni comprobantes.
    El admin lo crea y lo marca como facturado o pagado; el cliente lo ve.

    `status`: pending · invoiced · paid. "Vencido" no se guarda: se calcula con
    `due_date` para que no quede desactualizado.
    """

    __tablename__ = "payment_milestones"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'invoiced', 'paid')", name="ck_payment_milestones_status"),
        CheckConstraint("currency IN ('PEN', 'USD')", name="ck_payment_milestones_currency"),
        CheckConstraint("amount > 0", name="ck_payment_milestones_amount"),
        Index("ix_payment_milestones_project", "project_id", "due_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    """Visible para el cliente: a que entregable corresponde o como se factura."""
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
