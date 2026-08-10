from app.common.schemas.base import ORMModel


class HardeningRuleRead(ORMModel):
    id: int
    code: str
    title: str
    category: str
    severity: str
    description: str
    verification_method: str


class RuleEvaluationRead(ORMModel):
    rule: HardeningRuleRead
    result: str
    evidence: str


class GapSummary(ORMModel):
    total: int
    passed: int
    failed: int
    manual: int
    not_applicable: int
    compliance_percent: float
