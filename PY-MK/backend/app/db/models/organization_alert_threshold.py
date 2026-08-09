from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrganizationAlertThreshold(Base):
    __tablename__ = "organization_alert_thresholds"
    __table_args__ = (
        CheckConstraint("overdue_days > 0", name="overdue_days_positive"),
        CheckConstraint("no_review_days > 0", name="no_review_days_positive"),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True
    )
    overdue_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    no_review_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    organization = relationship("Organization", back_populates="alert_thresholds")
