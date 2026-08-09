from datetime import date, datetime
from typing import Literal

from pydantic import Field

from app.common.schemas.base import ORMModel

AssetType = Literal["hardware", "software", "information", "service", "people", "facility"]
Treatment = Literal["mitigate", "transfer", "avoid", "accept"]
RiskStatus = Literal["identified", "assessed", "treated", "accepted", "closed"]


class RiskAssetBase(ORMModel):
    client_id: int
    device_id: int | None = None
    name: str = Field(min_length=1, max_length=160)
    asset_type: AssetType
    confidentiality: int = Field(ge=1, le=5)
    integrity: int = Field(ge=1, le=5)
    availability: int = Field(ge=1, le=5)
    owner_user_id: int | None = None


class RiskAssetCreate(RiskAssetBase):
    pass


class RiskAssetUpdate(ORMModel):
    device_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=160)
    asset_type: AssetType | None = None
    confidentiality: int | None = Field(default=None, ge=1, le=5)
    integrity: int | None = Field(default=None, ge=1, le=5)
    availability: int | None = Field(default=None, ge=1, le=5)
    owner_user_id: int | None = None


class RiskAssetRead(RiskAssetBase):
    id: int
    business_value: int
    created_at: datetime
    updated_at: datetime


class RiskBase(ORMModel):
    client_id: int
    asset_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    threat: str | None = Field(default=None, max_length=200)
    vulnerability: str | None = Field(default=None, max_length=200)
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    treatment: Treatment | None = None
    residual_likelihood: int | None = Field(default=None, ge=1, le=5)
    residual_impact: int | None = Field(default=None, ge=1, le=5)
    residual_score: int | None = Field(default=None, ge=1, le=25)
    status: RiskStatus = "identified"
    owner_user_id: int | None = None
    review_date: date | None = None


class RiskCreate(RiskBase):
    threat_ids: list[int] = Field(default_factory=list)
    vulnerability_ids: list[int] = Field(default_factory=list)


class RiskUpdate(ORMModel):
    asset_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    threat: str | None = Field(default=None, max_length=200)
    vulnerability: str | None = Field(default=None, max_length=200)
    likelihood: int | None = Field(default=None, ge=1, le=5)
    impact: int | None = Field(default=None, ge=1, le=5)
    treatment: Treatment | None = None
    residual_likelihood: int | None = Field(default=None, ge=1, le=5)
    residual_impact: int | None = Field(default=None, ge=1, le=5)
    residual_score: int | None = Field(default=None, ge=1, le=25)
    status: RiskStatus | None = None
    owner_user_id: int | None = None
    review_date: date | None = None


class CatalogEntryBase(ORMModel):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=500)
    category: str = Field(min_length=1, max_length=50)


class CatalogEntryCreate(CatalogEntryBase):
    pass


class CatalogEntryRead(CatalogEntryBase):
    id: int
    is_global: bool


class RiskAssociationsUpdate(ORMModel):
    threat_ids: list[int] = Field(default_factory=list)
    vulnerability_ids: list[int] = Field(default_factory=list)


class RiskRead(RiskBase):
    id: int
    inherent_score: int
    created_at: datetime
    updated_at: datetime
    threats: list[CatalogEntryRead] = Field(default_factory=list)
    vulnerabilities: list[CatalogEntryRead] = Field(default_factory=list)


class HeatmapCell(ORMModel):
    likelihood: int
    impact: int
    risks: list[RiskRead]
