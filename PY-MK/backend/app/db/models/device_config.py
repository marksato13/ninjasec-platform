from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DeviceConfig(Base):
    __tablename__ = "device_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    vendor_detected: Mapped[str] = mapped_column(String(30), nullable=False)
    raw_config: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_json: Mapped[str] = mapped_column(Text, nullable=False)
    parse_warnings: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    device = relationship("Device")
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by])
