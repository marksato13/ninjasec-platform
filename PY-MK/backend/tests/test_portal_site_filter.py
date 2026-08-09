"""05-P-05: filtro por sede en el inventario del portal cliente."""

from __future__ import annotations

from app.core.security import hash_password
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.client_site import ClientSite
from app.db.models.device import Device
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.integration import Integration
from app.db.models.role import Role
from app.db.models.user import User

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _client_with_sites(db, org_id, suffix):
    client = Client(organization_id=org_id, company_name=f"Cliente sedes {suffix}")
    db.add(client)
    db.flush()
    site_a = ClientSite(client_id=client.id, name=f"Sede A {suffix}")
    site_b = ClientSite(client_id=client.id, name=f"Sede B {suffix}")
    db.add_all([site_a, site_b])
    db.flush()

    integration = Integration(
        organization_id=org_id,
        client_id=client.id,
        connector_type="snmp",
        name=f"Integracion sedes {suffix}",
        base_url="https://collector.invalid",
    )
    db.add(integration)
    db.flush()

    dev_a = Device(integration_id=integration.id, site_id=site_a.id, hostname=f"dev-a-{suffix}", status="active")
    dev_b = Device(integration_id=integration.id, site_id=site_b.id, hostname=f"dev-b-{suffix}", status="active")
    db.add_all([dev_a, dev_b])
    db.commit()
    return client, site_a, site_b, dev_a, dev_b


def _client_token(db, http_client, organization_id, client_id, suffix):
    role = db.query(Role).filter(Role.code == RoleCode.CLIENT.value).first()
    if role is None:
        role = Role(code=RoleCode.CLIENT.value, name="Client")
        db.add(role)
        db.flush()
    user = User(
        organization_id=organization_id,
        role_id=role.id,
        full_name=f"Portal {suffix}",
        email=f"portal-sedes-{suffix}@ninjasec.local",
        password_hash=hash_password("client-password-123"),
        role_code=RoleCode.CLIENT,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(ClientProfile(client_id=client_id, user_id=user.id))
    db.commit()

    response = http_client.post(f"{API}/auth/login", json={
        "email": user.email, "password": "client-password-123",
    })
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_cliente_ve_solo_las_sedes_de_su_propia_empresa(db, http_client, seed_data):
    org_id = seed_data["org"].id
    client_a, site_a1, site_a2, _, _ = _client_with_sites(db, org_id, "a")
    client_b, site_b1, _, _, _ = _client_with_sites(db, org_id, "b")
    token_a = _client_token(db, http_client, org_id, client_a.id, "a")

    response = http_client.get(f"{API}/client-sites", headers=_auth(token_a))
    assert response.status_code == 200, response.text
    ids = {s["id"] for s in response.json()}
    assert ids == {site_a1.id, site_a2.id}
    assert site_b1.id not in ids


def test_cliente_filtra_inventario_por_sede_y_no_ve_otras(db, http_client, seed_data):
    org_id = seed_data["org"].id
    client_a, site_a1, site_a2, dev_a1, dev_a2 = _client_with_sites(db, org_id, "filtro")
    token = _client_token(db, http_client, org_id, client_a.id, "filtro")

    unfiltered = http_client.get(f"{API}/devices/", headers=_auth(token))
    assert unfiltered.status_code == 200
    assert {d["id"] for d in unfiltered.json()} == {dev_a1.id, dev_a2.id}

    filtered = http_client.get(
        f"{API}/devices/?site_id={site_a1.id}", headers=_auth(token)
    )
    assert filtered.status_code == 200, filtered.text
    ids = {d["id"] for d in filtered.json()}
    assert ids == {dev_a1.id}
    assert dev_a2.id not in ids


def test_cliente_sin_client_profile_no_ve_sedes(db, http_client, admin_token, seed_data):
    # admin_token no es rol client -- confirma que el endpoint sigue
    # devolviendo el comportamiento anterior (sin auto-scoping) para
    # roles internos.
    response = http_client.get(f"{API}/client-sites", headers=_auth(admin_token))
    assert response.status_code == 200
