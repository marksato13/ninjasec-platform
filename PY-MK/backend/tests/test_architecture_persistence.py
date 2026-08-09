"""Pruebas independientes de persistencia para el repositorio de arquitectura.

El módulo 27-P1 aún no está disponible en todas las ramas.  Al incorporarse,
estas pruebas ejercitan sus entidades directamente para que no dependan de
estado ni de rutas creadas por otros módulos.
"""

import pytest
from sqlalchemy import select

from app.db.models.client import Client
from app.db.models.enums import ClientStatus


architecture = pytest.importorskip(
    "app.db.models.architecture",
    reason="El repositorio de arquitectura (27-P1) todavía no está instalado.",
)
ArchitectureElement = architecture.ArchitectureElement
ArchitectureModel = architecture.ArchitectureModel
ArchitectureRelationship = architecture.ArchitectureRelationship


LAYERS = ("motivation", "business", "application", "technology", "implementation")
RELATIONSHIP_TYPES = (
    "serving",
    "assignment",
    "realization",
    "composition",
    "flow",
    "triggering",
    "association",
)


def _client(db, organization_id: int, suffix: str) -> Client:
    client = Client(
        organization_id=organization_id,
        company_name=f"Arquitectura {suffix}",
        commercial_status=ClientStatus.ACTIVE,
    )
    db.add(client)
    db.flush()
    return client


def _model(db, client_id: int, organization_id: int, *, state: str = "baseline") -> ArchitectureModel:
    model = ArchitectureModel(
        client_id=client_id,
        organization_id=organization_id,
        name=f"Modelo {state}",
        version="1.0",
        state=state,
        adm_phase="D",
        status="draft",
    )
    db.add(model)
    db.flush()
    return model


def test_model_crud_persists_each_architecture_state(db, seed_data):
    """Los tres estados se conservan y un modelo puede editarse y eliminarse."""
    client = _client(db, seed_data["org"].id, "Estados")
    models = [_model(db, client.id, client.organization_id, state=state) for state in ("baseline", "target", "transition")]
    db.commit()

    db.expire_all()
    persisted = db.scalars(
        select(ArchitectureModel).where(ArchitectureModel.client_id == client.id)
    ).all()
    assert {model.state for model in persisted} == {"baseline", "target", "transition"}

    target = next(model for model in persisted if model.state == "target")
    target.name = "Modelo objetivo aprobado"
    target.status = "approved"
    db.commit()
    db.expire_all()
    assert db.get(ArchitectureModel, target.id).name == "Modelo objetivo aprobado"
    assert db.get(ArchitectureModel, target.id).status == "approved"

    transition_id = next(model.id for model in models if model.state == "transition")
    db.delete(db.get(ArchitectureModel, transition_id))
    db.commit()
    assert db.get(ArchitectureModel, transition_id) is None


@pytest.mark.parametrize("layer", LAYERS)
def test_layer_filter_returns_only_requested_layer(db, seed_data, layer):
    """Cada consulta de capa es exclusiva aunque el modelo contenga las cinco."""
    client = _client(db, seed_data["org"].id, f"Capas {layer}")
    model = _model(db, client.id, client.organization_id)
    elements = [
        ArchitectureElement(
            model_id=model.id,
            layer=current_layer,
            element_type="TestElement",
            name=f"Elemento {current_layer}",
        )
        for current_layer in LAYERS
    ]
    db.add_all(elements)
    db.commit()

    filtered = db.scalars(
        select(ArchitectureElement).where(
            ArchitectureElement.model_id == model.id,
            ArchitectureElement.layer == layer,
        )
    ).all()

    assert [element.name for element in filtered] == [f"Elemento {layer}"]
    assert {element.layer for element in filtered} == {layer}


def test_element_crud_preserves_source_traceability(db, seed_data):
    """La procedencia de un elemento derivado sobrevive a create, update y reload."""
    client = _client(db, seed_data["org"].id, "Trazabilidad")
    model = _model(db, client.id, client.organization_id)
    element = ArchitectureElement(
        model_id=model.id,
        layer="technology",
        element_type="Device",
        name="Firewall perimetral",
        description="Inventario sincronizado",
        source_module="devices",
        source_id="42",
        properties_json={"ip_address": "10.0.0.1"},
    )
    db.add(element)
    db.commit()

    db.expire_all()
    persisted = db.get(ArchitectureElement, element.id)
    assert (persisted.source_module, persisted.source_id) == ("devices", "42")
    assert persisted.properties_json == {"ip_address": "10.0.0.1"}

    persisted.name = "Firewall principal"
    db.commit()
    db.expire_all()
    updated = db.get(ArchitectureElement, element.id)
    assert updated.name == "Firewall principal"
    assert (updated.source_module, updated.source_id) == ("devices", "42")

    db.delete(updated)
    db.commit()
    assert db.get(ArchitectureElement, element.id) is None


def test_relationship_crud_preserves_actual_relationship_types(db, seed_data):
    """Los tipos definidos por P1 se almacenan literalmente, sin asumir validación P3."""
    client = _client(db, seed_data["org"].id, "Relaciones")
    model = _model(db, client.id, client.organization_id)
    source = ArchitectureElement(
        model_id=model.id, layer="application", element_type="ApplicationComponent", name="Origen"
    )
    target = ArchitectureElement(
        model_id=model.id, layer="technology", element_type="Node", name="Destino"
    )
    db.add_all([source, target])
    db.flush()
    relationships = [
        ArchitectureRelationship(
            model_id=model.id,
            source_element_id=source.id,
            target_element_id=target.id,
            relationship_type=relationship_type,
            label=f"Etiqueta {relationship_type}",
        )
        for relationship_type in RELATIONSHIP_TYPES
    ]
    db.add_all(relationships)
    db.commit()

    db.expire_all()
    persisted = db.scalars(
        select(ArchitectureRelationship).where(
            ArchitectureRelationship.source_element_id == source.id,
            ArchitectureRelationship.target_element_id == target.id,
        )
    ).all()
    assert {relationship.relationship_type for relationship in persisted} == set(RELATIONSHIP_TYPES)

    relationship = next(item for item in persisted if item.relationship_type == "flow")
    relationship.label = "Flujo actualizado"
    db.commit()
    db.expire_all()
    assert db.get(ArchitectureRelationship, relationship.id).label == "Flujo actualizado"

    db.delete(db.get(ArchitectureRelationship, relationship.id))
    db.commit()
    assert db.get(ArchitectureRelationship, relationship.id) is None

    # La validación legal de pares ArchiMate 3.2 es P3 y no existe en P1:
    # esta prueba sólo verifica los tipos que el modelo realmente persiste.
