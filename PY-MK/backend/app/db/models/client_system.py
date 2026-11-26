from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time_utils import utcnow
from app.db.base import Base

ESTADOS_SISTEMA = ("en_construccion", "en_produccion", "en_mantenimiento", "retirado")
PLANES_SOPORTE = ("ninguno", "basico", "profesional", "a_medida")
TIPOS_ENTORNO = ("dev", "staging", "prod")


def _en(valores: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in valores)


class ClientSystem(Base):
    """Un sistema que Ninja Dev entregó o mantiene para un cliente (35-P-01).

    Un proyecto termina; el sistema sigue. Entornos, despliegues y soporte
    cuelgan de aquí, y el proyecto solo dice "este proyecto lo construyó".

    `support_plan` es solo el nombre del plan: los precios viven en el repo
    privado de la empresa, nunca aquí.
    """

    __tablename__ = "client_systems"
    __table_args__ = (
        CheckConstraint(f"status IN ({_en(ESTADOS_SISTEMA)})", name="status"),
        CheckConstraint(f"support_plan IN ({_en(PLANES_SOPORTE)})", name="support_plan"),
        Index("ix_client_systems_client", "organization_id", "client_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    stack: Mapped[str | None] = mapped_column(String(160), nullable=True)
    repository_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    """Interno: el cliente no lo ve."""
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="en_construccion")
    warranty_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    support_plan: Mapped[str] = mapped_column(String(20), nullable=False, default="ninguno")
    origin_project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    environments = relationship(
        "ClientSystemEnvironment",
        back_populates="system",
        cascade="all, delete-orphan",
        order_by="ClientSystemEnvironment.id",
    )


class ClientSystemEnvironment(Base):
    """Un entorno (dev, staging o prod) de un sistema del cliente.

    `secrets_location` dice DÓNDE están las claves ("gestor de la empresa,
    entrada X"), nunca cuáles son: la API rechaza valores con forma de secreto.
    """

    __tablename__ = "client_system_environments"
    __table_args__ = (
        CheckConstraint(f"kind IN ({_en(TIPOS_ENTORNO)})", name="kind"),
        UniqueConstraint("system_id", "kind", name="uq_client_system_environments_kind"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    system_id: Mapped[int] = mapped_column(
        ForeignKey("client_systems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hosting: Mapped[str | None] = mapped_column(String(120), nullable=True)
    domain_expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    certificate_expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    secrets_location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    """Interno: el cliente no lo ve."""
    visible_to_client: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    system = relationship("ClientSystem", back_populates="environments")
