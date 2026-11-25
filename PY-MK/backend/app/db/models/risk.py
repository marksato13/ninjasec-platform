from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time_utils import utcnow
from app.db.base import Base

risk_threats = Table(
    "risk_threats",
    Base.metadata,
    Column("risk_id", ForeignKey("risks.id", ondelete="CASCADE"), primary_key=True),
    Column("threat_id", ForeignKey("threats.id", ondelete="RESTRICT"), primary_key=True),
)
risk_vulnerabilities = Table(
    "risk_vulnerabilities",
    Base.metadata,
    Column("risk_id", ForeignKey("risks.id", ondelete="CASCADE"), primary_key=True),
    Column("vulnerability_id", ForeignKey("vulnerabilities.id", ondelete="RESTRICT"), primary_key=True),
)


class Threat(Base):
    """25-P2: catálogo reutilizable (ISO 27005/MAGERIT). ``organization_id``
    nulo = entrada global visible por todas las organizaciones, siguiendo el
    mismo patrón que ``Skill``/``DocType``."""

    __tablename__ = "threats"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_threat_org_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_global: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_vulnerability_org_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_global: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class RiskAsset(Base):
    __tablename__ = "risk_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(30), nullable=False)
    confidentiality: Mapped[int] = mapped_column(Integer, nullable=False)
    integrity: Mapped[int] = mapped_column(Integer, nullable=False)
    availability: Mapped[int] = mapped_column(Integer, nullable=False)
    business_value: Mapped[int] = mapped_column(Integer, nullable=False)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    client = relationship("Client")
    device = relationship("Device")
    owner_user = relationship("User", foreign_keys=[owner_user_id])
    risks = relationship("Risk", back_populates="asset", cascade="all, delete-orphan")


class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int] = mapped_column(ForeignKey("risk_assets.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    threat: Mapped[str | None] = mapped_column(String(200), nullable=True)
    vulnerability: Mapped[str | None] = mapped_column(String(200), nullable=True)
    likelihood: Mapped[int] = mapped_column(Integer, nullable=False)
    impact: Mapped[int] = mapped_column(Integer, nullable=False)
    inherent_score: Mapped[int] = mapped_column(Integer, nullable=False)
    treatment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    residual_likelihood: Mapped[int | None] = mapped_column(Integer, nullable=True)
    residual_impact: Mapped[int | None] = mapped_column(Integer, nullable=True)
    residual_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="identified")
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    client = relationship("Client")
    asset = relationship("RiskAsset", back_populates="risks")
    owner_user = relationship("User", foreign_keys=[owner_user_id])
    threats: Mapped[list[Threat]] = relationship(secondary=risk_threats, lazy="selectin")
    vulnerabilities: Mapped[list[Vulnerability]] = relationship(secondary=risk_vulnerabilities, lazy="selectin")
