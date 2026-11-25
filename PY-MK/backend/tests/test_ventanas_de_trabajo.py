"""Ventanas de trabajo (auditoria funcional 2026-11-25, C2).

El tecnico pide, el cliente del proyecto autoriza por escrito, el equipo ejecuta y
cierra. Nadie ve ni toca ventanas de proyectos ajenos: responde 404.
"""

from __future__ import annotations

import importlib
from datetime import timedelta
from uuid import uuid4

import pytest

from app.core.security import create_access_token
from app.core.time_utils import utcnow
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.enums import RoleCode, UserStatus
from app.db.models.organization import Organization
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.user import User
from tests.conftest import API

MIGRACION = "app.db.migrations.versions.20261128_02_ventanas_de_trabajo"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _usuario(db, org_id: int, role_id: int, rol: RoleCode) -> User:
    s = uuid4().hex[:8]
    u = User(
        organization_id=org_id,
        role_id=role_id,
        full_name=f"{rol.value} {s}",
        email=f"{rol.value.lower()}-{s}@example.com",
        password_hash="x",
        role_code=rol,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(u)
    db.flush()
    return u


def _token(u: User) -> str:
    return create_access_token(u.email, extra={"role": u.role_code.value})


@pytest.fixture
def mundo(db, seed_data):
    org = seed_data["org"]
    s = uuid4().hex[:8]
    cliente = Client(organization_id=org.id, company_name=f"Pyme {s}")
    otro_cliente = Client(organization_id=org.id, company_name=f"Otra pyme {s}")
    db.add_all([cliente, otro_cliente])
    db.flush()
    proyecto = Project(organization_id=org.id, client_id=cliente.id, name=f"Firewall {s}")
    db.add(proyecto)
    db.flush()
    rol = seed_data["collab"].role_id
    usuario_cliente = _usuario(db, org.id, rol, RoleCode.CLIENT)
    db.add(ClientProfile(client_id=cliente.id, user_id=usuario_cliente.id))
    cliente_ajeno = _usuario(db, org.id, rol, RoleCode.CLIENT)
    db.add(ClientProfile(client_id=otro_cliente.id, user_id=cliente_ajeno.id))
    db.add(ProjectMember(project_id=proyecto.id, user_id=seed_data["collab"].id))
    colaborador_fuera = _usuario(db, org.id, rol, RoleCode.COLLABORATOR)
    db.commit()
    return {
        "proyecto": proyecto,
        "cliente": _token(usuario_cliente),
        "cliente_ajeno": _token(cliente_ajeno),
        "colaborador_fuera": _token(colaborador_fuera),
    }


def _pedido(proyecto_id: int, horas: int = 96, **extra) -> dict:
    inicio = utcnow() + timedelta(hours=horas)
    return {
        "project_id": proyecto_id,
        "title": "Cambio de reglas del firewall",
        "change_description": "Reordenar reglas y cerrar el puerto 3389 hacia internet",
        "systems_affected": "FortiGate principal",
        "impact": "high",
        "rollback_plan": "Restaurar el respaldo de configuracion tomado antes del cambio",
        "starts_at": inicio.isoformat(),
        "ends_at": (inicio + timedelta(hours=2)).isoformat(),
        **extra,
    }


def _pedir(http_client, token, cuerpo):
    return http_client.post(f"{API}/work-windows/", json=cuerpo, headers=_auth(token))


def test_ciclo_completo_pedir_aprobar_ejecutar_cerrar(http_client, collaborator_token, mundo):
    r = _pedir(http_client, collaborator_token, _pedido(mundo["proyecto"].id))
    assert r.status_code == 201, r.text
    vid = r.json()["id"]
    assert r.json()["status"] == "requested"

    r = http_client.post(
        f"{API}/work-windows/{vid}/decision", json={"approve": True}, headers=_auth(mundo["cliente"])
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "approved" and r.json()["client_decision_at"]

    for estado in ("in_progress", "completed"):
        r = http_client.post(
            f"{API}/work-windows/{vid}/status", json={"status": estado}, headers=_auth(collaborator_token)
        )
        assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"


def test_sin_72_horas_de_anticipacion_da_422(http_client, collaborator_token, mundo):
    r = _pedir(http_client, collaborator_token, _pedido(mundo["proyecto"].id, horas=24))
    assert r.status_code == 422


def test_la_emergencia_solo_la_pide_un_admin(http_client, collaborator_token, admin_token, mundo):
    cuerpo = _pedido(mundo["proyecto"].id, horas=1, is_emergency=True)
    assert _pedir(http_client, collaborator_token, cuerpo).status_code == 403
    assert _pedir(http_client, admin_token, cuerpo).status_code == 201


def test_no_se_puede_ejecutar_sin_aprobacion_del_cliente(http_client, collaborator_token, mundo):
    vid = _pedir(http_client, collaborator_token, _pedido(mundo["proyecto"].id)).json()["id"]
    r = http_client.post(
        f"{API}/work-windows/{vid}/status", json={"status": "in_progress"}, headers=_auth(collaborator_token)
    )
    assert r.status_code == 409


def test_el_equipo_no_puede_aprobar_por_el_cliente(http_client, admin_token, collaborator_token, mundo):
    vid = _pedir(http_client, collaborator_token, _pedido(mundo["proyecto"].id)).json()["id"]
    r = http_client.post(f"{API}/work-windows/{vid}/decision", json={"approve": True}, headers=_auth(admin_token))
    assert r.status_code == 403


def test_rechazar_exige_comentario(http_client, collaborator_token, mundo):
    vid = _pedir(http_client, collaborator_token, _pedido(mundo["proyecto"].id)).json()["id"]
    url = f"{API}/work-windows/{vid}/decision"
    assert http_client.post(url, json={"approve": False}, headers=_auth(mundo["cliente"])).status_code == 422
    r = http_client.post(url, json={"approve": False, "comment": "Ese dia hay cierre de mes"},
                         headers=_auth(mundo["cliente"]))
    assert r.status_code == 200 and r.json()["status"] == "rejected"


def test_cliente_de_otra_empresa_no_ve_ni_aprueba(http_client, collaborator_token, mundo):
    vid = _pedir(http_client, collaborator_token, _pedido(mundo["proyecto"].id)).json()["id"]
    ajeno = _auth(mundo["cliente_ajeno"])
    assert http_client.get(f"{API}/work-windows/{vid}", headers=ajeno).status_code == 404
    assert http_client.post(f"{API}/work-windows/{vid}/decision", json={"approve": True},
                            headers=ajeno).status_code == 404
    assert vid not in {v["id"] for v in http_client.get(f"{API}/work-windows/", headers=ajeno).json()}
    propio = http_client.get(f"{API}/work-windows/", headers=_auth(mundo["cliente"])).json()
    assert vid in {v["id"] for v in propio}


def test_colaborador_que_no_es_miembro_no_pide_ni_ve(http_client, collaborator_token, mundo):
    fuera = _auth(mundo["colaborador_fuera"])
    assert _pedir(http_client, mundo["colaborador_fuera"], _pedido(mundo["proyecto"].id)).status_code == 404
    vid = _pedir(http_client, collaborator_token, _pedido(mundo["proyecto"].id)).json()["id"]
    assert http_client.get(f"{API}/work-windows/{vid}", headers=fuera).status_code == 404


def test_proyecto_de_otra_organizacion_da_404(http_client, admin_token, db):
    s = uuid4().hex[:8]
    org = Organization(name=f"Ajena {s}", slug=f"ajena-{s}")
    db.add(org)
    db.flush()
    proyecto = Project(organization_id=org.id, name=f"Ajeno {s}")
    db.add(proyecto)
    db.commit()
    assert _pedir(http_client, admin_token, _pedido(proyecto.id)).status_code == 404


def test_volver_atras_exige_nota(http_client, collaborator_token, mundo):
    vid = _pedir(http_client, collaborator_token, _pedido(mundo["proyecto"].id)).json()["id"]
    http_client.post(f"{API}/work-windows/{vid}/decision", json={"approve": True}, headers=_auth(mundo["cliente"]))
    url = f"{API}/work-windows/{vid}/status"
    http_client.post(url, json={"status": "in_progress"}, headers=_auth(collaborator_token))
    assert http_client.post(url, json={"status": "rolled_back"}, headers=_auth(collaborator_token)).status_code == 422
    r = http_client.post(url, json={"status": "rolled_back", "note": "El enlace no volvio; se restauro"},
                         headers=_auth(collaborator_token))
    assert r.status_code == 200 and r.json()["execution_note"]


def test_la_migracion_encadena_y_coincide_con_el_modelo():
    from app.db.base import Base

    m = importlib.import_module(MIGRACION)
    assert (m.revision, m.down_revision) == ("20261128_02", "20261128_01")
    assert "work_windows" in Base.metadata.tables
