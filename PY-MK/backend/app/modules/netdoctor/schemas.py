from app.common.schemas.base import ORMModel


class NetdoctorIssueRead(ORMModel):
    id: int
    code: str
    title: str
    category: str
    severity: str
    symptoms: str
    probable_causes: str
    diagnostic_commands: dict
    remediation: str


class GuidedTreeNode(ORMModel):
    id: str
    question: str | None = None
    issue_code: str | None = None
    options: list[dict] | None = None
