from app.common.schemas.base import ORMModel


class CollaboratorRead(ORMModel):
    id: int
    user_id: int
    position_title: str | None = None
    bio: str | None = None
    skills_json: str | None = None
    seniority: str | None = None
    availability_status: str | None = None
    area: str | None = None
    photo_url: str | None = None
    portfolio_url: str | None = None
    phone: str | None = None
    cv_url: str | None = None
    source_application_id: int | None = None


class CollaboratorUpdate(ORMModel):
    position_title: str | None = None
    bio: str | None = None
    skills_json: str | None = None
    seniority: str | None = None
    availability_status: str | None = None
    area: str | None = None
    photo_url: str | None = None
    portfolio_url: str | None = None
    phone: str | None = None
    cv_url: str | None = None


class CollaboratorCreate(ORMModel):
    user_id: int
    position_title: str | None = None
    bio: str | None = None
    skills_json: str | None = None
    seniority: str | None = None
    availability_status: str | None = None
    area: str | None = None
    photo_url: str | None = None
    portfolio_url: str | None = None
