from datetime import datetime
from typing import Literal

from pydantic import Field

from app.common.schemas.base import ORMModel


BusinessLine = Literal["sec", "dev"]


class AreaRead(ORMModel):
    id: int
    name: str
    slug: str
    is_active: bool
    business_line: BusinessLine | None = None
    created_at: datetime | None = None


class AreaCreate(ORMModel):
    name: str = Field(min_length=2, max_length=120)
    # El slug se deriva del nombre si no se envia: quien administra
    # catalogos no tiene por que saber que es un slug.
    slug: str | None = Field(default=None, max_length=120)
    business_line: BusinessLine | None = None


class AreaUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    is_active: bool | None = None
    # Enviar null la deja vacia (el area cuenta para los dos modos).
    business_line: BusinessLine | None = None
    confirm_deactivation: bool = False
