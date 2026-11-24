from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import ProjectStatus


class Project(Base):
    __tablename__ = "projects"

    __table_args__ = (
        Index("ix_projects_org", "organization_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id"), nullable=True
    )
    project_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_types.id"), nullable=True
    )
    area_id: Mapped[int | None] = mapped_column(ForeignKey("areas.id"), nullable=True)
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id"), nullable=True
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status_enum"), default=ProjectStatus.PLANNING
    )
    phase: Mapped[str] = mapped_column(String(20), nullable=False, default="diagnostico", server_default="diagnostico")
    """Fase del recorrido (app/core/fases.py). Distinta de `status`: el estado dice si el
    proyecto corre, esta dice POR DONDE va."""
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    budget_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    organization = relationship("Organization", back_populates="projects")
    client = relationship("Client", back_populates="projects")
    project_type = relationship("ProjectType", back_populates="projects")
    area = relationship("Area", back_populates="projects")
    service = relationship("Service")
    product = relationship("Product", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project")
    docs = relationship("ProjectDoc", back_populates="project")
    requirements = relationship("ProjectRequirement", back_populates="project")
    recommendations = relationship("ProjectRecommendation", back_populates="project")
    tasks = relationship("ProjectTask", back_populates="project")
