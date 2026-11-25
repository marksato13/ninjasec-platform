from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time_utils import utcnow
from app.db.base import Base


class ProjectUpdate(Base):
    """Una entrada de la bitacora de un proyecto.

    Es lo que alimenta la linea de tiempo que ve el cliente: un cambio de fase, un
    hito, un avance escrito por el especialista o una tarea terminada.

    `visible_to_client` es explicito y por defecto verdadero para lo que genera el
    sistema (cambios de fase, tareas hechas). Una nota interna se escribe con
    visible_to_client = False y el cliente no la ve nunca.
    """

    __tablename__ = "project_updates"
    __table_args__ = (Index("ix_project_updates_project_created", "project_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    author_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="update")
    """update · phase_change · milestone · task_done  (String, no Enum nativo: el
    conjunto puede crecer sin una migracion; la validacion va en el esquema)."""
    phase: Mapped[str | None] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    link_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    """Para desarrollo: el entorno de pruebas o la demo que el cliente puede abrir."""
    visible_to_client: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)


class ProjectDevice(Base):
    """Un equipo sobre el que se trabaja en este proyecto."""

    __tablename__ = "project_devices"
    __table_args__ = (UniqueConstraint("project_id", "device_id", name="uq_project_device"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
