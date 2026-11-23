from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Service(Base):
    __tablename__ = "services"

    # El slug era `unique=True` de una sola columna sobre una tabla que lleva
    # organization_id NOT NULL. Consecuencia: el primer cliente que creara un
    # servicio "pentest-web" se quedaba ese slug para toda la plataforma, y
    # ninguna otra organizacion podia volver a usarlo.
    #
    # Es exactamente el mismo fallo que la migracion 20260806_01 corrigio para
    # areas, project_types y products, y al que `services` se le paso.
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_service_org_slug"),
        Index("ix_services_org", "organization_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    area_id: Mapped[int | None] = mapped_column(ForeignKey("areas.id"), nullable=True)
    project_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_types.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    price_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    organization = relationship("Organization", back_populates="services")
    area = relationship("Area", back_populates="services")
    project_type = relationship("ProjectType", back_populates="services")
    requests = relationship("ServiceRequest", back_populates="service")
    client_services = relationship("ClientService", back_populates="service")
