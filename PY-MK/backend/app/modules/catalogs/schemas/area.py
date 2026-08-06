from datetime import datetime

from pydantic import Field

from app.common.schemas.base import ORMModel


class AreaRead(ORMModel):
    id: int
    name: str
    slug: str
    is_active: bool
    created_at: datetime | None = None


class AreaCreate(ORMModel):
    name: str = Field(min_length=2, max_length=120)
    # El slug se deriva del nombre si no se envia: quien administra
    # catalogos no tiene por que saber que es un slug.
    slug: str | None = Field(default=None, max_length=120)


class AreaUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    is_active: bool | None = None
