from datetime import datetime

from app.common.schemas.base import ORMModel


class AuditLogRead(ORMModel):
    id: int
    user_id: int | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    created_at: datetime
    metadata_json: str | None = None
