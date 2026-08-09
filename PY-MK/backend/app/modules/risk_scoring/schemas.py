from app.common.schemas.base import ORMModel


class ExternalReputationDetail(ORMModel):
    source: str
    score: int
    category: str


class HostScoreRead(ORMModel):
    ip_address: str
    internal_alert_count: int
    internal_score: int
    external_score: int
    composite_score: int
    external_sources: list[ExternalReputationDetail]
