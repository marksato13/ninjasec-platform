from datetime import datetime
from typing import Literal

from app.common.schemas.base import ORMModel

Layer = Literal["motivation", "business", "application", "technology", "implementation"]
State = Literal["baseline", "target", "transition"]
RelationshipType = Literal["serving", "assignment", "realization", "composition", "flow", "triggering", "association"]


class ElementCreate(ORMModel):
    layer: Layer
    element_type: str
    name: str
    description: str | None = None
    source_module: str | None = None
    source_id: str | None = None
    properties_json: dict | None = None


class ElementUpdate(ORMModel):
    layer: Layer | None = None
    element_type: str | None = None
    name: str | None = None
    description: str | None = None
    source_module: str | None = None
    source_id: str | None = None
    properties_json: dict | None = None


class ElementRead(ElementCreate):
    id: int
    model_id: int


class RelationshipCreate(ORMModel):
    source_element_id: int
    target_element_id: int
    relationship_type: RelationshipType
    label: str | None = None


class RelationshipUpdate(ORMModel):
    relationship_type: RelationshipType | None = None
    label: str | None = None


class RelationshipRead(RelationshipCreate):
    id: int
    model_id: int


class ModelCreate(ORMModel):
    client_id: int
    name: str
    version: str = "1.0"
    state: State
    adm_phase: str | None = None
    status: Literal["draft", "approved", "superseded"] = "draft"


class ModelUpdate(ORMModel):
    name: str | None = None
    version: str | None = None
    state: State | None = None
    adm_phase: str | None = None
    status: Literal["draft", "approved", "superseded"] | None = None


class ModelRead(ModelCreate):
    id: int
    organization_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    elements: list[ElementRead] = []
    relationships: list[RelationshipRead] = []
