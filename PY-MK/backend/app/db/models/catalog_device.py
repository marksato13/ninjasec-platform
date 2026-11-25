from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time_utils import utcnow
from app.db.base import Base


class CatalogDevice(Base):
    """Catálogo de modelos de equipos de red (no instancias -- ver `Device`).

    Sin `organization_id` a propósito: es un catálogo global compartido por
    todas las organizaciones, igual que `Skill`/`DocType`/`Role` (ver
    CLAUDE.md § Multi-tenancy, "excepciones globales por diseño").
    """

    __tablename__ = "catalog_devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String(30), nullable=True)
    osi_layer: Mapped[str | None] = mapped_column(String(10), nullable=True)
    segment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    port_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    port_speed: Mapped[str | None] = mapped_column(String(30), nullable=True)
    poe: Mapped[bool] = mapped_column(Boolean, default=False)
    poe_budget_w: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stackable: Mapped[bool] = mapped_column(Boolean, default=False)
    rack_mountable: Mapped[bool] = mapped_column(Boolean, default=False)
    managed: Mapped[bool] = mapped_column(Boolean, default=False)
    switching_capacity_gbps: Mapped[float | None] = mapped_column(nullable=True)
    throughput_mbps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_consumption_w: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lifecycle_status: Mapped[str] = mapped_column(String(20), default="active")
    eos_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    eol_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    price_range_usd: Mapped[str | None] = mapped_column(String(40), nullable=True)
    use_cases: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # Regla de copyright del módulo 19: se enlaza al datasheet oficial del
    # fabricante, nunca se rehospeda el PDF en la plataforma.
    datasheet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )
