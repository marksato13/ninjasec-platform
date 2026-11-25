from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time_utils import utcnow
from app.db.base import Base

RESULTADOS_DESPLIEGUE = ("ok", "fallido", "revertido")


class ClientSystemDeployment(Base):
    """Un despliegue de un sistema del cliente a uno de sus entornos (35-P-02).

    Sustituye el "¿qué versión tiene producción?" por un dato.

    `environment_kind` es una copia del tipo del entorno en el momento del
    despliegue: si el entorno se quita después, la historia no se pierde ni
    cambia de significado (`environment_id` pasa a NULL).

    El checklist (respaldo, prueba de humo, plan de vuelta atrás) es interno:
    el cliente nunca lo ve.
    """

    __tablename__ = "client_system_deployments"
    __table_args__ = (
        CheckConstraint("result IN ('ok', 'fallido', 'revertido')", name="result"),
        CheckConstraint("environment_kind IN ('dev', 'staging', 'prod')", name="environment_kind"),
        Index("ix_client_system_deployments_system_at", "system_id", "deployed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    system_id: Mapped[int] = mapped_column(
        ForeignKey("client_systems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    environment_id: Mapped[int | None] = mapped_column(
        ForeignKey("client_system_environments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    environment_kind: Mapped[str] = mapped_column(String(10), nullable=False)
    version: Mapped[str] = mapped_column(String(60), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    """Qué cambió, en lenguaje de cliente."""
    deployed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    deployed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    backup_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    smoke_test_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rollback_plan_written: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rollback_plan: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result: Mapped[str] = mapped_column(String(12), nullable=False, default="ok")
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    published_update_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_updates.id", ondelete="SET NULL"), nullable=True
    )
    """El avance "Versión X publicada" en la bitácora del proyecto; evita publicarlo dos veces."""
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
