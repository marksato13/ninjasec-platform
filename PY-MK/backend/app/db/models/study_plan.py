"""Planes de estudio: la ruta que lleva a una certificación.

Por qué existe, y por qué no se cuelga de lo que ya había:

- `UserCertification` ya guarda **la meta** (NSE 4, CCNA) y su estado. Lo que
  no guardaba es **el camino**: qué hay que estudiar, en qué orden y por
  dónde vas.
- `UserSkill` guarda qué sabe alguien, no qué está aprendiendo.
- `recruitment` **no tiene `organization_id`**, así que colgar de ahí un plan
  de estudio heredaría esa fuga. Estas tablas llevan el suyo propio.

Decisión de diseño, tomada el 2026-11-23: **el plan se define por área y se
asigna a una persona.** Sirve para una sola persona estudiando hoy y escala a
varios colaboradores sin rehacer el modelo.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time_utils import utcnow
from app.db.base import Base


class StudyPlan(Base):
    """Una ruta de aprendizaje. Por ejemplo «Fortinet NSE 4» o «CCNA 200-301»."""

    __tablename__ = "study_plans"
    __table_args__ = (
        # Compuesta con la organización, no global. `services.slug` era único
        # en toda la tabla y eso dejaba que un cliente le bloqueara el nombre
        # a otro -- y de paso le confirmara que existe. No se repite aquí.
        UniqueConstraint("organization_id", "slug", name="uq_study_plan_org_slug"),
        Index("ix_study_plans_org", "organization_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    area: Mapped[str] = mapped_column(String(80), nullable=False)
    """Redes, Ciberseguridad, Desarrollo… El eje por el que se agrupan."""

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    target_certification: Mapped[str | None] = mapped_column(String(150), nullable=True)
    """A qué certificación lleva. Coincide con `user_certifications.name`
    cuando la hay, para poder cerrar el círculo al aprobar."""

    vendor: Mapped[str | None] = mapped_column(String(80), nullable=True)
    """Fortinet, Cisco, pfSense… Útil para filtrar y para el informe."""

    exam_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    """200-301, NSE4_FGT-7.6… El código con el que se compra el examen."""

    estimated_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    modules = relationship(
        "StudyModule",
        back_populates="plan",
        order_by="StudyModule.position",
        cascade="all, delete-orphan",
    )
    enrollments = relationship("StudyEnrollment", back_populates="plan")


class StudyModule(Base):
    """Un bloque del plan. Se estudia en orden, de `position` menor a mayor."""

    __tablename__ = "study_modules"
    __table_args__ = (
        UniqueConstraint("plan_id", "position", name="uq_study_module_plan_pos"),
        Index("ix_study_modules_plan", "plan_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False
    )

    position: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Qué tienes que SABER HACER al terminarlo, no qué tienes que leer.
    Un objetivo que no se puede demostrar no sirve para medir progreso."""

    topics: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Los puntos concretos, uno por línea. Texto y no JSON a propósito: se
    lee y se edita a mano, y aquí no hace falta consultarlo por campo."""

    lab: Mapped[str | None] = mapped_column(Text, nullable=True)
    """El laboratorio que lo demuestra. Sin práctica no hay NSE4 ni CCNA."""

    estimated_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    """Cuánto pesa en el examen real, si el fabricante lo publica. Sirve para
    decidir dónde meter las horas cuando van justas."""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    plan = relationship("StudyPlan", back_populates="modules")
    progress = relationship(
        "StudyProgress", back_populates="module", cascade="all, delete-orphan"
    )


class StudyEnrollment(Base):
    """Una persona siguiendo un plan, con sus fechas."""

    __tablename__ = "study_enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "plan_id", name="uq_study_enrollment_user_plan"),
        Index("ix_study_enrollments_org", "organization_id"),
        Index("ix_study_enrollments_user", "user_id"),
        Index("ix_study_enrollments_plan", "plan_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("study_plans.id"), nullable=False)

    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    """Cuándo quieres presentarte. Es lo que convierte el plan en un plan."""

    weekly_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    """Horas que piensas dedicar por semana. Con esto y las horas estimadas
    se puede decir si la fecha objetivo es realista o es un deseo."""

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    plan = relationship("StudyPlan", back_populates="enrollments")
    user = relationship("User", foreign_keys=[user_id])
    progress = relationship(
        "StudyProgress", back_populates="enrollment", cascade="all, delete-orphan"
    )


class StudyProgress(Base):
    """Cómo vas en un módulo concreto.

    El estado lo marca quien estudia. `validated_by` existe para cuando hay
    un tutor: sin tutor, un módulo completado se queda en COMPLETED y eso ya
    es suficiente. Con tutor, pasa a VALIDATED.

    Esa fue la segunda decisión de diseño: que funcione igual en solitario y
    supervisado, sin dos modelos distintos.
    """

    __tablename__ = "study_progress"
    __table_args__ = (
        UniqueConstraint(
            "enrollment_id", "module_id", name="uq_study_progress_enrollment_module"
        ),
        Index("ix_study_progress_enrollment", "enrollment_id"),
        Index("ix_study_progress_module", "module_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("study_enrollments.id", ondelete="CASCADE"), nullable=False
    )
    module_id: Mapped[int] = mapped_column(
        ForeignKey("study_modules.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    """pending · in_progress · completed · validated.

    String y no Enum nativo a propósito: añadir un valor a un Enum de
    PostgreSQL exige una migración, y este conjunto todavía puede moverse
    mientras el módulo se asienta. La validación va en el esquema Pydantic,
    que es donde se puede cambiar sin tocar la base.
    """

    hours_spent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    """Captura del laboratorio, repositorio, nota del simulacro. Opcional:
    exigir evidencia para avanzar es la forma más rápida de que nadie use
    esto."""

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    validated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    enrollment = relationship("StudyEnrollment", back_populates="progress")
    module = relationship("StudyModule", back_populates="progress")
    validator = relationship("User", foreign_keys=[validated_by])
