"""01-P-05 y 13-P-04: escalación de privilegios y aislamiento cross-tenant."""

from __future__ import annotations

from app.core.security import create_access_token, hash_password
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.user import User

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _role(db, code, name):
    role = db.query(Role).filter(Role.code == code).first()
    if role is None:
        role = Role(code=code, name=name)
        db.add(role)
        db.flush()
    return role


def _user(db, org_id, role_code, suffix):
    role = _role(db, role_code.value, role_code.value)
    user = User(
        organization_id=org_id,
        role_id=role.id,
        full_name=f"Usuario {suffix}",
        email=f"seguridad-{suffix}@ninjasec.local",
        password_hash=hash_password("unused"),
        role_code=role_code,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user, create_access_token(user.email)


def _super_admin(db, org_id, suffix="super"):
    return _user(db, org_id, RoleCode.SUPER_ADMIN, suffix)


def _admin(db, org_id, suffix="admin"):
    return _user(db, org_id, RoleCode.ADMIN, suffix)


# --- 01-P-05: escalación de privilegios en create_user ---------------------


def test_admin_no_puede_crear_super_admin(db, http_client, seed_data):
    org_id = seed_data["org"].id
    _, admin_token = _admin(db, org_id, "esc-1")

    response = http_client.post(
        f"{API}/users/",
        headers=_auth(admin_token),
        json={
            "organization_id": org_id,
            "role_code": "super_admin",
            "full_name": "Intento de escalación",
            "email": "escalacion@ninjasec.local",
            "password": "SuperSecreta123!",
        },
    )
    assert response.status_code == 403


def test_admin_no_puede_crear_otro_admin(db, http_client, seed_data):
    org_id = seed_data["org"].id
    _, admin_token = _admin(db, org_id, "esc-2")

    response = http_client.post(
        f"{API}/users/",
        headers=_auth(admin_token),
        json={
            "organization_id": org_id,
            "role_code": "admin",
            "full_name": "Otro admin",
            "email": "otro-admin@ninjasec.local",
            "password": "SuperSecreta123!",
        },
    )
    assert response.status_code == 403


def test_admin_si_puede_crear_collaborator(db, http_client, seed_data):
    org_id = seed_data["org"].id
    _, admin_token = _admin(db, org_id, "esc-3")
    _role(db, RoleCode.COLLABORATOR.value, "Collaborator")

    response = http_client.post(
        f"{API}/users/",
        headers=_auth(admin_token),
        json={
            "organization_id": org_id,
            "role_code": "collaborator",
            "full_name": "Colaborador normal",
            "email": "colaborador-normal@ninjasec.local",
            "password": "SuperSecreta123!",
        },
    )
    assert response.status_code == 201, response.text


def test_super_admin_si_puede_crear_super_admin(db, http_client, seed_data):
    org_id = seed_data["org"].id
    _, super_token = _super_admin(db, org_id, "esc-4")

    response = http_client.post(
        f"{API}/users/",
        headers=_auth(super_token),
        json={
            "organization_id": org_id,
            "role_code": "super_admin",
            "full_name": "Segundo super admin",
            "email": "segundo-super@ninjasec.local",
            "password": "SuperSecreta123!",
        },
    )
    assert response.status_code == 201, response.text


# --- 13-P-04: aislamiento cross-tenant en update/delete ---------------------


def test_admin_no_puede_editar_usuario_de_otra_organizacion(db, http_client, seed_data):
    org_a = seed_data["org"].id
    org_b = Organization(name="Tenant usuarios ajeno", slug="tenant-usuarios-ajeno")
    db.add(org_b)
    db.flush()
    db.commit()

    _, admin_a_token = _admin(db, org_a, "cross-1")
    victim, _ = _admin(db, org_b.id, "cross-2")

    response = http_client.put(
        f"{API}/users/{victim.id}",
        headers=_auth(admin_a_token),
        json={"full_name": "Nombre cambiado sin permiso"},
    )
    assert response.status_code == 404


def test_super_admin_no_puede_eliminar_usuario_de_otra_organizacion(db, http_client, seed_data):
    org_a = seed_data["org"].id
    org_b = Organization(name="Tenant usuarios ajeno 2", slug="tenant-usuarios-ajeno-2")
    db.add(org_b)
    db.flush()
    db.commit()

    _, super_a_token = _super_admin(db, org_a, "cross-3")
    victim, _ = _admin(db, org_b.id, "cross-4")

    response = http_client.delete(f"{API}/users/{victim.id}", headers=_auth(super_a_token))
    assert response.status_code == 404

    # El usuario sigue existiendo -- no se borró nada de otra organización.
    still_there = http_client.put(
        f"{API}/users/{victim.id}",
        headers=_auth(super_a_token),
        json={"full_name": "sigue existiendo"},
    )
    assert still_there.status_code == 404


def test_admin_sigue_pudiendo_editar_dentro_de_su_organizacion(db, http_client, seed_data):
    org_id = seed_data["org"].id
    _, admin_token = _admin(db, org_id, "cross-5")
    _role(db, RoleCode.COLLABORATOR.value, "Collaborator")
    target, _ = _user(db, org_id, RoleCode.COLLABORATOR, "cross-6")

    response = http_client.put(
        f"{API}/users/{target.id}",
        headers=_auth(admin_token),
        json={"full_name": "Nombre actualizado legítimamente"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["full_name"] == "Nombre actualizado legítimamente"
