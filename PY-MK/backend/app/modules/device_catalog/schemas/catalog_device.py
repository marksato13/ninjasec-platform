from datetime import date, datetime

from app.common.schemas.base import ORMModel


class CatalogDeviceRead(ORMModel):
    id: int
    slug: str
    brand: str
    model: str
    category: str
    subcategory: str | None = None
    osi_layer: str | None = None
    segment: str | None = None
    port_count: int | None = None
    port_speed: str | None = None
    poe: bool
    poe_budget_w: int | None = None
    stackable: bool
    rack_mountable: bool
    managed: bool
    switching_capacity_gbps: float | None = None
    throughput_mbps: int | None = None
    power_consumption_w: int | None = None
    lifecycle_status: str
    eos_date: date | None = None
    eol_date: date | None = None
    price_range_usd: str | None = None
    use_cases: str | None = None
    tags: str | None = None
    datasheet_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CatalogDeviceUpdate(ORMModel):
    # Sin `slug`: es estable e inmutable una vez creado (ver 29-P1).
    brand: str | None = None
    model: str | None = None
    lifecycle_status: str | None = None
    eos_date: date | None = None
    eol_date: date | None = None
    price_range_usd: str | None = None
    datasheet_url: str | None = None


class CatalogDeviceCreate(ORMModel):
    slug: str
    brand: str
    model: str
    category: str
    subcategory: str | None = None
    osi_layer: str | None = None
    segment: str | None = None
    port_count: int | None = None
    port_speed: str | None = None
    poe: bool = False
    poe_budget_w: int | None = None
    stackable: bool = False
    rack_mountable: bool = False
    managed: bool = False
    switching_capacity_gbps: float | None = None
    throughput_mbps: int | None = None
    power_consumption_w: int | None = None
    lifecycle_status: str = "active"
    eos_date: date | None = None
    eol_date: date | None = None
    price_range_usd: str | None = None
    use_cases: str | None = None
    tags: str | None = None
    datasheet_url: str | None = None
