from datetime import datetime

from pydantic import field_validator, model_validator

from app.common.schemas.base import ORMModel


class UserSkillRead(ORMModel):
    id: int
    user_id: int
    skill_id: int
    skill_name: str | None = None
    level: str | None = None
    status: str
    verified_by: int | None = None
    verified_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime | None = None


class UserSkillCreate(ORMModel):
    skill_id: int
    level: str | None = None
    user_id: int | None = None


class UserSkillUpdate(ORMModel):
    level: str | None = None


class UserSkillVerify(ORMModel):
    status: str
    rejection_reason: str | None = None

    @field_validator("rejection_reason")
    @classmethod
    def normalize_rejection_reason(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def require_rejection_reason(self) -> "UserSkillVerify":
        if self.status == "rejected" and not self.rejection_reason:
            raise ValueError("El motivo de rechazo es obligatorio")
        return self
