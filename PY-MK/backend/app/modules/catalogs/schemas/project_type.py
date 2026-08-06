from datetime import datetime

from pydantic import Field

from app.common.schemas.base import ORMModel


class ProjectTypeRead(ORMModel):
    id: int
    name: str
    slug: str
    is_active: bool
    created_at: datetime | None = None


class ProjectTypeCreate(ORMModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(default=None, max_length=120)


class ProjectTypeUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    is_active: bool | None = None
