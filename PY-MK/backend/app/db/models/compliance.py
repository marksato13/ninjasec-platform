from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time_utils import utcnow
from app.db.base import Base


class ComplianceFramework(Base):
    """Catálogo de marcos normativos (ISO 27001, etc). Global -- no lleva
    organization_id, igual que el resto de catálogos de referencia."""

    __tablename__ = "compliance_frameworks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)

    controls = relationship("ComplianceControl", back_populates="framework")


class ComplianceControl(Base):
    """Catálogo global de controles de un marco (ej. los 93 del Anexo A de
    ISO 27001:2022). Sin organization_id: es el mismo catálogo para todas
    las organizaciones. El estado por cliente vive en ClientControlStatus."""

    __tablename__ = "compliance_controls"
    __table_args__ = (
        UniqueConstraint("framework_id", "code", name="uq_compliance_control_framework_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    framework_id: Mapped[int] = mapped_column(
        ForeignKey("compliance_frameworks.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    parent_code: Mapped[str] = mapped_column(String(10), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)

    framework = relationship("ComplianceFramework", back_populates="controls")


class ClientControlStatus(Base):
    """Fila editable de la Declaración de Aplicabilidad (SoA) para un
    cliente concreto sobre un control concreto."""

    __tablename__ = "client_control_status"
    __table_args__ = (
        UniqueConstraint("client_id", "control_id", name="uq_client_control_status_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    control_id: Mapped[int] = mapped_column(
        ForeignKey("compliance_controls.id", ondelete="CASCADE"), nullable=False
    )
    applicability: Mapped[str] = mapped_column(String(20), default="applicable")
    implementation_status: Mapped[str] = mapped_column(String(20), default="not_implemented")
    maturity_level: Mapped[int] = mapped_column(Integer, default=0)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsible_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    client = relationship("Client")
    control = relationship("ComplianceControl")
    responsible_user = relationship("User", foreign_keys=[responsible_user_id])
