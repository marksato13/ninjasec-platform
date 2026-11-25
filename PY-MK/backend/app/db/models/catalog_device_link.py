from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time_utils import utcnow
from app.db.base import Base


class CatalogDeviceLink(Base):
    """Enlaces oficiales de un modelo del catálogo (29-P2).

    Nunca se rehospeda el documento -- `url` apunta siempre al sitio del
    fabricante. `archive_url` es el respaldo en Wayback Machine para
    cuando el enlace oficial se cae (frecuente en Cisco/Huawei).
    """

    __tablename__ = "catalog_device_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    catalog_device_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_devices.id"), nullable=False
    )
    link_type: Mapped[str] = mapped_column(String(30), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    archive_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
