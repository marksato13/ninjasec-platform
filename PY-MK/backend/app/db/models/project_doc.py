from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time_utils import utcnow
from app.db.base import Base
from app.db.models.enums import DocStatus, DocVisibility


class ProjectDoc(Base):
    __tablename__ = "project_docs"

    __table_args__ = (
        Index("ix_project_docs_project", "project_id"),
        CheckConstraint(
            "client_decision IS NULL OR client_decision IN ('approved', 'changes_requested')",
            name="ck_project_docs_client_decision",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    doc_type_id: Mapped[int] = mapped_column(ForeignKey("doc_types.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(400), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    preview_md: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    visibility: Mapped[DocVisibility] = mapped_column(
        Enum(DocVisibility, name="doc_visibility_enum"),
        default=DocVisibility.INTERNAL,
    )
    status: Mapped[DocStatus] = mapped_column(
        Enum(DocStatus, name="doc_status_enum"),
        default=DocStatus.DRAFT,
    )
    enabled: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    verified_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # C1: el cliente aprueba el entregable o pide cambios. Se vacia cuando el
    # equipo sube una version nueva, para que el cliente la vuelva a revisar.
    client_decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    client_decision_note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    client_decision_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    client_decision_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    project = relationship("Project", back_populates="docs")
    doc_type = relationship("DocType", back_populates="docs")
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    verified_by_user = relationship("User", foreign_keys=[verified_by])
