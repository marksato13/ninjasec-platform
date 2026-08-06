from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    # 20-P-09 — `organization_id` es NOT NULL aqui, asi que la unicidad
    # compuesta si cierra del todo: dos organizaciones pueden tener cada
    # una su producto "Firewall Gestionado" sin pisarse.
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_product_org_slug"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    area_id: Mapped[int | None] = mapped_column(ForeignKey("areas.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="products")
    area = relationship("Area", back_populates="products")
    projects = relationship("Project", back_populates="product")
