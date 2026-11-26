"""La topologia incluye los equipos registrados a mano.

Un equipo dado de alta desde el inventario no tiene integracion: cuelga de una
sede del cliente. Con la capsula de telemetria apagada no hay integraciones, y
el diagrama salia vacio aunque el inventario listara los equipos. Estas
pruebas fijan que la topologia cuenta los mismos equipos que el inventario y
que la sede no abre una puerta a otro cliente ni a otra organizacion.
"""

from __future__ import annotations

from app.db.models.client import Client
from app.db.models.client_site import ClientSite
from app.db.models.device import Device
from app.db.models.device_connection import DeviceConnection
from app.db.models.organization import Organization

API = "/api/v1"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _cliente_con_equipos_manuales(db, organization_id: int, prefijo: str):
    cliente = Client(organization_id=organization_id, company_name=f"Cliente {prefijo}")
    db.add(cliente)
    db.flush()
    sede = ClientSite(client_id=cliente.id, name=f"Sede {prefijo}")
    db.add(sede)
    db.flush()
    router = Device(site_id=sede.id, hostname=f"rt-{prefijo}", device_type="router", status="online")
    switch = Device(site_id=sede.id, hostname=f"sw-{prefijo}", device_type="switch", status="online")
    db.add_all([router, switch])
    db.flush()
    db.add(DeviceConnection(source_device_id=router.id, target_device_id=switch.id, link_type="ethernet"))
    db.commit()
    return cliente, sede, router, switch


def test_equipos_sin_integracion_aparecen_en_la_topologia(db, http_client, admin_token, seed_data):
    cliente, sede, router, switch = _cliente_con_equipos_manuales(db, seed_data["org"].id, "Manual")

    r = http_client.get(f"{API}/devices/topology?client_id={cliente.id}", headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    datos = r.json()
    assert {n["id"] for n in datos["nodes"]} == {router.id, switch.id}
    assert [(e["source"], e["target"]) for e in datos["edges"]] == [(router.id, switch.id)]
    assert datos["clusters"] == [
        {"label": "Sede Manual", "site_id": sede.id, "node_ids": [router.id, switch.id]}
    ]


def test_el_listado_de_conexiones_incluye_las_de_equipos_manuales(db, http_client, admin_token, seed_data):
    cliente, _, router, switch = _cliente_con_equipos_manuales(db, seed_data["org"].id, "Conexiones")

    r = http_client.get(f"{API}/device-connections/?client_id={cliente.id}", headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    assert [(c["source_device_id"], c["target_device_id"]) for c in r.json()] == [(router.id, switch.id)]


def test_la_sede_de_otro_cliente_no_se_cuela(db, http_client, admin_token, seed_data):
    propio, _, router, switch = _cliente_con_equipos_manuales(db, seed_data["org"].id, "Propio")
    _, _, ajeno_rt, ajeno_sw = _cliente_con_equipos_manuales(db, seed_data["org"].id, "Vecino")

    r = http_client.get(f"{API}/devices/topology?client_id={propio.id}", headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    ids = {n["id"] for n in r.json()["nodes"]}
    assert ids == {router.id, switch.id}
    assert not ids & {ajeno_rt.id, ajeno_sw.id}


def test_la_sede_de_otra_organizacion_no_se_cuela(db, http_client, admin_token, seed_data):
    """Un cliente ajeno con el mismo id de sede no aporta equipos: la sede se
    filtra por cliente y por organizacion a la vez."""
    org_ajena = Organization(name="Org Topologia Manual Ajena", slug="topo-manual-ajena")
    db.add(org_ajena)
    db.commit()
    ajeno, _, _, _ = _cliente_con_equipos_manuales(db, org_ajena.id, "Ajeno")

    r = http_client.get(f"{API}/devices/topology?client_id={ajeno.id}", headers=_auth(admin_token))
    assert r.status_code == 404

    r = http_client.get(f"{API}/device-connections/?client_id={ajeno.id}", headers=_auth(admin_token))
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert r.json() == []


def test_equipo_con_integracion_y_sede_no_se_duplica(db, http_client, admin_token, seed_data):
    from app.db.models.integration import Integration

    cliente, sede, router, _ = _cliente_con_equipos_manuales(db, seed_data["org"].id, "Mixto")
    integ = Integration(
        organization_id=seed_data["org"].id, client_id=cliente.id, connector_type="snmp",
        name="Integracion Mixto", base_url="https://collector.invalid",
    )
    db.add(integ)
    db.flush()
    router.integration_id = integ.id
    db.commit()

    r = http_client.get(f"{API}/devices/topology?client_id={cliente.id}", headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    ids = [n["id"] for n in r.json()["nodes"]]
    assert ids.count(router.id) == 1
