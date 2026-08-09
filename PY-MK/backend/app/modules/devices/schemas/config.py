from datetime import datetime

from app.common.schemas.base import ORMModel


class DeviceConfigRead(ORMModel):
    id: int
    device_id: int
    vendor_detected: str
    parsed_json: str
    parse_warnings: str | None = None
    uploaded_by: int
    uploaded_at: datetime | None = None
    has_raw_config: bool = False


class DeviceConfigCreate(ORMModel):
    device_id: int
    vendor_detected: str
    parsed_json: str
    parse_warnings: str | None = None
    raw_config: str | None = None
