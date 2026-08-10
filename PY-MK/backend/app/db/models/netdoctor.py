from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NetdoctorIssue(Base):
    """28-P1: catálogo global de problemas comunes de networking, con
    síntomas, causas probables y comandos de diagnóstico por vendor.

    Sin conexión SSH real en esta fase (28-P3, Tanda 4, gated por
    seguridad) -- el comando se muestra como texto para que el ingeniero
    lo ejecute manualmente."""

    __tablename__ = "netdoctor_issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    probable_causes: Mapped[str] = mapped_column(Text, nullable=False)
    # {"cisco_ios": "...", "mikrotik": "...", "huawei": "...", "ubiquiti": "..."}
    diagnostic_commands: Mapped[dict] = mapped_column(JSON, nullable=False)
    remediation: Mapped[str] = mapped_column(Text, nullable=False)
