from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Area(Base):
    __tablename__ = "areas"

    # 20-P-09 — La unicidad es por organizacion, no global.
    # Con `unique=True` en la columna, la primera organizacion que creaba
    # un area "Redes" se la quedaba para siempre: ninguna otra podia tener
    # la suya. El multi-tenant se rompia al segundo tenant.
    #
    # Nota: en Postgres los NULL son distintos entre si, asi que esta
    # restriccion no impide dos catalogos globales con el mismo nombre.
    # Los globales vienen del seed, que si es controlado.
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_area_org_name"),
        UniqueConstraint("organization_id", "slug", name="uq_area_org_slug"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    services = relationship("Service", back_populates="area")
    products = relationship("Product", back_populates="area")
    projects = relationship("Project", back_populates="area")
