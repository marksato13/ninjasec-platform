from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CatalogDeviceSummary(Base):
    """Resumen ejecutivo de elaboración propia de un modelo (29-P2).

    Es contenido original de Ninja Tech, no una copia del datasheet del
    fabricante -- ver la regla de copyright en
    PLANIFICACION/29-MODULO-CATALOGO-EQUIPOS.md. `source_note` cita de
    dónde se sacó la información (ej. "Datasheet oficial Cisco, 2024").

    Uno por modelo (`catalog_device_id` único) -- se edita, no se
    versiona en esta fase.
    """

    __tablename__ = "catalog_device_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    catalog_device_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_devices.id"), unique=True, nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
