from app.common.schemas.base import ORMModel


class HealthScoreBreakdownItem(ORMModel):
    category: str
    count: int
    deduction: int


class HealthScoreRead(ORMModel):
    client_id: int
    client_name: str
    score: int
    label: str
    narrative: str
    breakdown: list[HealthScoreBreakdownItem]
