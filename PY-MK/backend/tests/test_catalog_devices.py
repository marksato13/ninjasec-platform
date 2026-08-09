"""29-P1: catálogo de equipos con filtros facetados."""

from __future__ import annotations

from uuid import uuid4

from app.db.models.catalog_device import CatalogDevice

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _seed_devices(db, suffix=None):
    suffix = suffix or uuid4().hex[:8]
    devices = [
        CatalogDevice(
            slug=f"test-cisco-switch-{suffix}", brand="Cisco", model="Test Switch",
            category="switch", poe=True, stackable=True, lifecycle_status="active",
        ),
        CatalogDevice(
            slug=f"test-mikrotik-router-{suffix}", brand="MikroTik", model="Test Router",
            category="router", poe=False, stackable=False, lifecycle_status="active",
        ),
        CatalogDevice(
            slug=f"test-cisco-eol-firewall-{suffix}", brand="Cisco", model="Test EOL Firewall",
            category="firewall", poe=False, stackable=False, lifecycle_status="eol",
        ),
    ]
    db.add_all(devices)
    db.commit()
    return devices


def test_lista_sin_filtros_devuelve_todo(db, http_client, admin_token, seed_data):
    devices = _seed_devices(db)
    response = http_client.get(f"{API}/catalog/devices/", headers=_auth(admin_token))
    assert response.status_code == 200, response.text
    slugs = {d["slug"] for d in response.json()}
    assert {d.slug for d in devices} <= slugs


def test_filtros_combinables_devuelven_el_subconjunto_correcto(
    db, http_client, admin_token, seed_data
):
    devices = _seed_devices(db)
    switch = devices[0]
    response = http_client.get(
        f"{API}/catalog/devices/?brand=Cisco&category=switch", headers=_auth(admin_token)
    )
    assert response.status_code == 200, response.text
    slugs = [d["slug"] for d in response.json()]
    assert switch.slug in slugs
    assert devices[1].slug not in slugs
    assert devices[2].slug not in slugs


def test_filtro_lifecycle_status_encuentra_equipos_eol(db, http_client, admin_token, seed_data):
    devices = _seed_devices(db)
    firewall = devices[2]
    response = http_client.get(
        f"{API}/catalog/devices/?lifecycle_status=eol", headers=_auth(admin_token)
    )
    assert response.status_code == 200, response.text
    slugs = {d["slug"] for d in response.json()}
    assert firewall.slug in slugs
    assert devices[0].slug not in slugs


def test_slug_duplicado_es_rechazado(db, http_client, admin_token, seed_data):
    devices = _seed_devices(db)
    response = http_client.post(
        f"{API}/catalog/devices/",
        headers=_auth(admin_token),
        json={
            "slug": devices[0].slug,
            "brand": "Cisco", "model": "Otro", "category": "switch",
        },
    )
    assert response.status_code == 400


def test_slug_no_se_puede_cambiar_al_actualizar(db, http_client, admin_token, seed_data):
    devices = _seed_devices(db)
    target = devices[0]
    original_slug = target.slug

    response = http_client.put(
        f"{API}/catalog/devices/{target.id}",
        headers=_auth(admin_token),
        json={"slug": "otro-slug-distinto", "brand": "Cisco Renombrado"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["slug"] == original_slug
    assert body["brand"] == "Cisco Renombrado"


def test_colaborador_puede_consultar_pero_no_crear(
    db, http_client, collaborator_token, seed_data
):
    _seed_devices(db)
    listed = http_client.get(f"{API}/catalog/devices/", headers=_auth(collaborator_token))
    assert listed.status_code == 200

    denied = http_client.post(
        f"{API}/catalog/devices/",
        headers=_auth(collaborator_token),
        json={"slug": f"no-deberia-crear-{uuid4().hex[:8]}", "brand": "X", "model": "Y", "category": "switch"},
    )
    assert denied.status_code == 403
