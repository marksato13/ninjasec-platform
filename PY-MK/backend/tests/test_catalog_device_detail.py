"""29-P2: ficha detallada + enlaces + resumen ejecutivo + cruce con inventario."""

from __future__ import annotations

from uuid import uuid4

from app.db.models.catalog_device import CatalogDevice
from app.db.models.device import Device
from app.db.models.integration import Integration

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _seed_device(db, suffix=None):
    suffix = suffix or uuid4().hex[:8]
    device = CatalogDevice(
        slug=f"test-detail-{suffix}", brand="Cisco", model=f"Test Model {suffix}",
        category="switch", poe=True, stackable=True, lifecycle_status="active",
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def test_detalle_incluye_links_summary_e_instance_count_vacios(db, http_client, admin_token, seed_data):
    device = _seed_device(db)
    response = http_client.get(f"{API}/catalog/devices/{device.id}", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["links"] == []
    assert body["summary"] is None
    assert body["instance_count"] == 0


def test_admin_agrega_y_elimina_un_link(db, http_client, admin_token, seed_data):
    device = _seed_device(db)
    created = http_client.post(
        f"{API}/catalog/devices/{device.id}/links",
        headers=_auth(admin_token),
        json={"link_type": "datasheet", "url": "https://example.com/datasheet.pdf"},
    )
    assert created.status_code == 201, created.text
    link_id = created.json()["id"]

    detail = http_client.get(f"{API}/catalog/devices/{device.id}", headers=_auth(admin_token))
    assert len(detail.json()["links"]) == 1

    deleted = http_client.delete(
        f"{API}/catalog/devices/{device.id}/links/{link_id}", headers=_auth(admin_token)
    )
    assert deleted.status_code == 204

    detail_after = http_client.get(f"{API}/catalog/devices/{device.id}", headers=_auth(admin_token))
    assert detail_after.json()["links"] == []


def test_colaborador_no_puede_agregar_links(db, http_client, collaborator_token, seed_data):
    device = _seed_device(db)
    response = http_client.post(
        f"{API}/catalog/devices/{device.id}/links",
        headers=_auth(collaborator_token),
        json={"link_type": "datasheet", "url": "https://example.com/x.pdf"},
    )
    assert response.status_code == 403


def test_colaborador_si_puede_redactar_el_resumen_ejecutivo(db, http_client, collaborator_token, seed_data):
    device = _seed_device(db)
    response = http_client.put(
        f"{API}/catalog/devices/{device.id}/summary",
        headers=_auth(collaborator_token),
        json={"content": "Resumen de prueba", "source_note": "Fuente de prueba"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["content"] == "Resumen de prueba"


def test_guardar_el_resumen_dos_veces_actualiza_en_vez_de_duplicar(db, http_client, admin_token, seed_data):
    device = _seed_device(db)
    http_client.put(
        f"{API}/catalog/devices/{device.id}/summary",
        headers=_auth(admin_token),
        json={"content": "Version 1"},
    )
    second = http_client.put(
        f"{API}/catalog/devices/{device.id}/summary",
        headers=_auth(admin_token),
        json={"content": "Version 2"},
    )
    assert second.status_code == 200
    detail = http_client.get(f"{API}/catalog/devices/{device.id}", headers=_auth(admin_token))
    assert detail.json()["summary"]["content"] == "Version 2"


def test_instance_count_cuenta_dispositivos_de_la_misma_marca_y_modelo(
    db, http_client, admin_token, seed_data
):
    device = _seed_device(db, suffix="conteo")
    integration = Integration(
        organization_id=seed_data["org"].id,
        connector_type="manual",
        name="Integracion de prueba",
        base_url="https://example.com",
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)

    db.add_all([
        Device(integration_id=integration.id, hostname="sw-1", vendor="cisco", model=device.model.lower()),
        Device(integration_id=integration.id, hostname="sw-2", vendor="CISCO", model=device.model.upper()),
        Device(integration_id=integration.id, hostname="sw-3", vendor="mikrotik", model="otro modelo"),
    ])
    db.commit()

    response = http_client.get(f"{API}/catalog/devices/{device.id}", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    assert response.json()["instance_count"] == 2, (
        "debe contar sin importar mayusculas/minusculas y excluir modelos distintos"
    )
