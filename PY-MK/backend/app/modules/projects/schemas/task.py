from datetime import datetime

from app.common.schemas.base import ORMModel


class ProjectTaskRead(ORMModel):
    id: int
    organization_id: int
    project_id: int
    project_name: str
    assigned_user_id: int
    assigned_user_name: str
    title: str
    description: str | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectTaskCreate(ORMModel):
    project_id: int
    assigned_user_id: int
    title: str
    description: str | None = None
    status: str = "pending"


class ProjectTaskUpdate(ORMModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    assigned_user_id: int | None = None
