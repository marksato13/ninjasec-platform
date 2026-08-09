from datetime import date, datetime

from pydantic import field_validator

from app.common.schemas.base import ORMModel

VALID_APPLICABILITY = {"applicable", "not_applicable"}
VALID_IMPLEMENTATION_STATUS = {"not_implemented", "planned", "partial", "implemented"}


class ControlStatusRead(ORMModel):
    control_id: int
    code: str
    parent_code: str
    category: str
    title: str
    applicability: str
    implementation_status: str
    maturity_level: int
    justification: str | None = None
    responsible_user_id: int | None = None
    responsible_user_name: str | None = None
    target_date: date | None = None
    updated_at: datetime | None = None


class SoaSummary(ORMModel):
    client_id: int
    framework: str
    total_controls: int
    applicable_controls: int
    implemented_controls: int
    compliance_percentage: float
    controls: list[ControlStatusRead]


class ControlStatusUpdate(ORMModel):
    applicability: str | None = None
    implementation_status: str | None = None
    maturity_level: int | None = None
    justification: str | None = None
    responsible_user_id: int | None = None
    target_date: date | None = None

    @field_validator("applicability")
    @classmethod
    def _valid_applicability(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_APPLICABILITY:
            raise ValueError(f"applicability debe ser uno de {sorted(VALID_APPLICABILITY)}")
        return value

    @field_validator("implementation_status")
    @classmethod
    def _valid_status(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_IMPLEMENTATION_STATUS:
            raise ValueError(
                f"implementation_status debe ser uno de {sorted(VALID_IMPLEMENTATION_STATUS)}"
            )
        return value

    @field_validator("maturity_level")
    @classmethod
    def _valid_maturity(cls, value: int | None) -> int | None:
        if value is not None and not (0 <= value <= 5):
            raise ValueError("maturity_level debe estar entre 0 y 5")
        return value
