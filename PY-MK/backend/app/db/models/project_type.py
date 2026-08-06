from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProjectType(Base):
    __tablename__ = "project_types"

    # 20-P-09 — Unicidad por organizacion. Ver la nota en area.py.
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_project_type_org_name"),
        UniqueConstraint("organization_id", "slug", name="uq_project_type_org_slug"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="project_type")
    services = relationship("Service", back_populates="project_type")
