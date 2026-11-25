from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time_utils import utcnow
from app.db.base import Base
from app.db.models.enums import CertificationStatus


class UserCertification(Base):
    __tablename__ = "user_certifications"

    __table_args__ = (
        Index("ix_user_certifications_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    credential_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[CertificationStatus] = mapped_column(
        Enum(CertificationStatus, name="cert_status_enum"),
        default=CertificationStatus.PENDING,
    )
    verified_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    # Area a la que aporta: "sec", "dev" o "both". Opcional (migracion 20261129_01).
    area: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # Certificado adjunto. Lo ven su duenio y los administradores; nunca el cliente.
    file_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="certifications")
    verified_by_user = relationship("User", foreign_keys=[verified_by])
