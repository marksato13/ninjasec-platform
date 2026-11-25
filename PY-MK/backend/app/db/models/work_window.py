"""Ventana de trabajo: permiso del cliente para tocar algo que puede cortar su servicio.

Flujo en ninjasec-empresa/OPERACIONES/flujos/03-VENTANA-DE-TRABAJO.md: el tecnico la
pide con 72 h de anticipacion, el cliente la aprueba o la rechaza por escrito, y el
tecnico registra como termino (completada o vuelta atras). Sin ventana aprobada no
se toca infraestructura del cliente.

Estado e impacto se guardan como texto y se validan con los enum de `enums.py`:
asi una migracion no tiene que crear tipos de PostgreSQL.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time_utils import utcnow
from app.db.base import Base


class WorkWindow(Base):
    __tablename__ = "work_windows"
    __table_args__ = (
        Index("ix_work_windows_org", "organization_id"),
        Index("ix_work_windows_project", "project_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    requested_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    change_description: Mapped[str] = mapped_column(Text, nullable=False)
    systems_affected: Mapped[str | None] = mapped_column(String(500), nullable=True)
    impact: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    rollback_plan: Mapped[str] = mapped_column(Text, nullable=False)
    is_emergency: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="requested")
    client_decision_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    client_decision_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    client_comment: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    execution_note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
