"""20-P-11: decisión explícita sobre qué puede leer el rol client de los
catálogos internos (áreas, tipos de proyecto, productos).

Investigado: el frontend de /portal nunca llama a estos endpoints (son
para armar/cotizar proyectos desde el backoffice). Antes se leían con
solo estar autenticado, sin ninguna regla de rol -- decisión: el rol
client no los necesita, se restringe.
"""

from __future__ import annotations

from app.core.security import create_access_token, hash_password
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.role import Role
from app.db.models.user import User

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _client_token(db, http_client, organization_id: int, suffix: str) -> str:
    role = db.query(Role).filter(Role.code == RoleCode.CLIENT.value).first()
    if role is None:
        role = Role(code=RoleCode.CLIENT.value, name="Client")
        db.add(role)
        db.flush()
    client = Client(organization_id=organization_id, company_name=f"Cliente {suffix}")
    db.add(client)
    db.flush()
    user = User(
        organization_id=organization_id,
        role_id=role.id,
        full_name=f"Portal {suffix}",
        email=f"portal-catalogos-{suffix}@ninjasec.local",
        password_hash=hash_password("client-password-123"),
        role_code=RoleCode.CLIENT,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(ClientProfile(client_id=client.id, user_id=user.id))
    db.commit()

    response = http_client.post(f"{API}/auth/login", json={
        "email": user.email, "password": "client-password-123",
    })
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_cliente_no_puede_leer_areas(db, http_client, seed_data):
    token = _client_token(db, http_client, seed_data["org"].id, "areas")
    response = http_client.get(f"{API}/areas", headers=_auth(token))
    assert response.status_code == 403


def test_cliente_no_puede_leer_project_types(db, http_client, seed_data):
    token = _client_token(db, http_client, seed_data["org"].id, "types")
    response = http_client.get(f"{API}/project-types", headers=_auth(token))
    assert response.status_code == 403


def test_cliente_no_puede_leer_productos(db, http_client, seed_data):
    token = _client_token(db, http_client, seed_data["org"].id, "products")
    response = http_client.get(f"{API}/products", headers=_auth(token))
    assert response.status_code == 403


def test_roles_internos_siguen_leyendo_los_catalogos(
    db, http_client, admin_token, collaborator_token
):
    for token in (admin_token, collaborator_token):
        for path in ("/areas", "/project-types", "/products"):
            response = http_client.get(f"{API}{path}", headers=_auth(token))
            assert response.status_code == 200, f"{path} con {token[:10]}...: {response.text}"
