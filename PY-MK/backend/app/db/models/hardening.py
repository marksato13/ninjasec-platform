from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HardeningRule(Base):
    """31-P1: catálogo global de reglas de hardening técnico (estilo CIS
    Benchmarks), verificables automáticamente contra datos reales del
    cliente o marcadas explícitamente como verificación manual.

    No confundir con `ComplianceControl` (módulo 24): aquel es la
    Declaración de Aplicabilidad manual de ISO 27001; esto es verificación
    técnica automática cruzando datos de integraciones/eventos reales.
    """

    __tablename__ = "hardening_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    # "auto" -> lo evalúa HardeningEvaluationService.CHECKS[check_key]
    # "manual" -> siempre se reporta como "manual", nunca pass/fail inventado
    verification_method: Mapped[str] = mapped_column(String(10), nullable=False)
    check_key: Mapped[str | None] = mapped_column(String(60), nullable=True)
