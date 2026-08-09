from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Audit(Base):
    """26-P1: encargo de auditoría formal (COBIT 2019 / ISO 19011).

    No confundir con AuditLog (modules/audit) -- aquel es el log técnico
    de eventos; esto es la gestión de auditorías como servicio
    profesional. El log es insumo probatorio de estas auditorías.
    """

    __tablename__ = "audits"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_audits_organization_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    framework: Mapped[str] = mapped_column(String(20), nullable=False)
    audit_type: Mapped[str] = mapped_column(String(20), nullable=False)
    lead_auditor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    planned_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    planned_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="planned")
    opinion: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    client = relationship("Client")
    lead_auditor = relationship("User", foreign_keys=[lead_auditor_id])
