from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time_utils import utcnow
from app.db.base import Base


class ArchitectureModel(Base):
    __tablename__ = "architecture_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False, default="1.0")
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    adm_phase: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    elements = relationship("ArchitectureElement", cascade="all, delete-orphan", back_populates="model")
    relationships = relationship("ArchitectureRelationship", cascade="all, delete-orphan", back_populates="model")


class ArchitectureElement(Base):
    __tablename__ = "architecture_elements"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("architecture_models.id", ondelete="CASCADE"), nullable=False, index=True)
    layer: Mapped[str] = mapped_column(String(24), nullable=False)
    element_type: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_module: Mapped[str | None] = mapped_column(String(80))
    source_id: Mapped[str | None] = mapped_column(String(80))
    properties_json: Mapped[dict | None] = mapped_column(JSON)

    model = relationship("ArchitectureModel", back_populates="elements")


class ArchitectureRelationship(Base):
    __tablename__ = "architecture_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("architecture_models.id", ondelete="CASCADE"), nullable=False, index=True)
    source_element_id: Mapped[int] = mapped_column(ForeignKey("architecture_elements.id", ondelete="CASCADE"), nullable=False)
    target_element_id: Mapped[int] = mapped_column(ForeignKey("architecture_elements.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(24), nullable=False)
    label: Mapped[str | None] = mapped_column(String(160))

    model = relationship("ArchitectureModel", back_populates="relationships")
