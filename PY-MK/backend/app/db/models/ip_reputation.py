from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IpReputationCache(Base):
    """30-P2: caché de reputación externa por IP y fuente.

    Evita agotar la cuota gratuita de AbuseIPDB/VirusTotal/GreyNoise
    consultando la misma IP en cada request -- ver `RiskScoringService`
    para el TTL de reutilización.
    """

    __tablename__ = "ip_reputation_cache"
    __table_args__ = (UniqueConstraint("ip_address", "source", name="uq_ip_reputation_ip_source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
