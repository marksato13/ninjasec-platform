from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NavVisibility(Base):
    """Una excepcion al menu por defecto: «esta opcion, para esta audiencia».

    Solo se guardan las DIFERENCIAS respecto a `app/core/navegacion.py`. Si
    una opcion se vuelve a dejar como estaba, la fila se borra. Asi la tabla
    cuenta lo que se ha tocado, no repite lo que ya viene de serie, y un
    cambio en los valores por defecto llega a quien no los modifico.

    Lleva `organization_id` y la unicidad lo incluye: cada organizacion edita
    sus propios menus sin ver ni pisar los de otra.
    """

    __tablename__ = "nav_visibility"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "surface", "item_key", "audience",
            name="uq_nav_visibility_org_surface_item_audience",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    surface: Mapped[str] = mapped_column(String(20), nullable=False)
    item_key: Mapped[str] = mapped_column(String(120), nullable=False)
    audience: Mapped[str] = mapped_column(String(20), nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # Sin ondelete: borrar un usuario no debe borrar el historial del menu, y
    # users ya tiene el problema documentado de audit_logs. Se deja NULL.
    updated_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
