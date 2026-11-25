"""35-P-01: sistemas del cliente y sus entornos.

- Admin: gestiona lo de su organización. Cliente y colaborador: solo leen.
- Colaborador: ve solo los sistemas cuyo proyecto de origen lo tiene como miembro.
- Cliente: solo los suyos, sin repository_url ni secrets_location, y solo los
  entornos visible_to_client.
- Lo ajeno (otro cliente, otra organización, inexistente): 404.
- secrets_location dice dónde está la clave, nunca la clave: 422.
- Solo se quita un sistema en construcción; lo demás se retira. Todo se audita.
"""

from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from app.db.models.audit_log import AuditLog
from app.db.models.client import Client
from app.db.models.client_system import ClientSystem, ClientSystemEnvironment
from app.db.models.organization import Organization
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.user import User
from tests.conftest import API
from tests.test_catalog_role_access import _client_token
from tests.test_cliente_no_ve_borradores import _auth, _proyecto_del_cliente

URL = f"{API}/client-systems"


def _cliente_y_proyecto(db, http_client, seed_data):
    sufijo = f"sis-{uuid4().hex[:6]}"
    token = _client_token(db, http_client, seed_data["org"].id, sufijo)
    return token, _proyecto_del_cliente(db, seed_data["org"].id, sufijo)


def _crear(http_client, admin_token, proyecto, **campos):
    cuerpo = {"client_id": proyecto.client_id, "name": "Tienda en línea", "origin_project_id": proyecto.id,
              "stack": "Next.js + FastAPI + PostgreSQL", "repository_url": "https://github.com/ejemplo/tienda",
              **campos}
    return http_client.post(URL, json=cuerpo, headers=_auth(admin_token))


def _entorno(http_client, admin_token, system_id, **campos):
    cuerpo = {"kind": "prod", "url": "https://tienda.example.com", "hosting": "Oracle Cloud",
              "secrets_location": "Gestor de la empresa, entrada Tienda/prod", **campos}
    return http_client.post(f"{URL}/{system_id}/environments", json=cuerpo, headers=_auth(admin_token))


def _sistema_con_entornos(db, http_client, seed_data, admin_token):
    token, proyecto = _cliente_y_proyecto(db, http_client, seed_data)
    r = _crear(http_client, admin_token, proyecto)
    assert r.status_code == 201, r.text
    sid = r.json()["id"]
    assert _entorno(http_client, admin_token, sid, visible_to_client=True).status_code == 201
    assert _entorno(http_client, admin_token, sid, kind="staging", url="https://staging.example.com").status_code == 201
    return token, proyecto, sid


def test_el_admin_crea_y_ve_todo(db, http_client, seed_data, admin_token):
    _, _, sid = _sistema_con_entornos(db, http_client, seed_data, admin_token)
    r = http_client.get(f"{URL}/{sid}", headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    ficha = r.json()
    assert ficha["can_manage"] is True
    assert ficha["repository_url"] == "https://github.com/ejemplo/tienda"
    assert {e["kind"] for e in ficha["environments"]} == {"prod", "staging"}
    assert all("secrets_location" in e for e in ficha["environments"])


def test_el_cliente_ve_solo_lo_suyo_y_sin_lo_interno(db, http_client, seed_data, admin_token):
    token, proyecto, sid = _sistema_con_entornos(db, http_client, seed_data, admin_token)
    _, ajeno = _cliente_y_proyecto(db, http_client, seed_data)
    _crear(http_client, admin_token, ajeno, name="Sistema de otro cliente")

    r = http_client.get(URL, headers=_auth(token))
    assert r.status_code == 200, r.text
    lista = r.json()
    assert lista["can_manage"] is False
    assert [s["id"] for s in lista["systems"]] == [sid]

    ficha = http_client.get(f"{URL}/{sid}", headers=_auth(token)).json()
    assert "repository_url" not in ficha and "origin_project_id" not in ficha
    assert [e["kind"] for e in ficha["environments"]] == ["prod"]  # staging no es visible
    assert "secrets_location" not in ficha["environments"][0]
    assert "visible_to_client" not in ficha["environments"][0]
    assert "Gestor" not in r.text and "github.com" not in r.text


def test_el_cliente_y_el_colaborador_no_gestionan(db, http_client, seed_data, admin_token, collaborator_token):
    token, proyecto, sid = _sistema_con_entornos(db, http_client, seed_data, admin_token)
    env_id = db.query(ClientSystemEnvironment.id).filter(ClientSystemEnvironment.system_id == sid).first()[0]
    for t in (token, collaborator_token):
        assert _crear(http_client, t, proyecto).status_code == 403
        assert http_client.put(f"{URL}/{sid}", json={"status": "retirado"}, headers=_auth(t)).status_code == 403
        assert http_client.delete(f"{URL}/{sid}", headers=_auth(t)).status_code == 403
        assert _entorno(http_client, t, sid, kind="dev").status_code == 403
        assert http_client.put(f"{URL}/environments/{env_id}", json={"visible_to_client": True},
                               headers=_auth(t)).status_code == 403
        assert http_client.delete(f"{URL}/environments/{env_id}", headers=_auth(t)).status_code == 403
    db.expire_all()
    assert db.get(ClientSystem, sid).status == "en_construccion"


def test_el_colaborador_ve_solo_los_de_sus_proyectos(db, http_client, seed_data, admin_token, collaborator_token):
    _, proyecto, sid = _sistema_con_entornos(db, http_client, seed_data, admin_token)
    _, otro = _cliente_y_proyecto(db, http_client, seed_data)
    otro_sid = _crear(http_client, admin_token, otro, name="Sistema sin el colaborador").json()["id"]

    # Aún no es miembro: no ve ninguno de los dos.
    assert http_client.get(f"{URL}/{sid}", headers=_auth(collaborator_token)).status_code == 404

    colab = db.query(User).filter(User.email == "test-collab@ninjasec.local").one()
    db.add(ProjectMember(project_id=proyecto.id, user_id=colab.id))
    db.commit()

    ids = [s["id"] for s in http_client.get(URL, headers=_auth(collaborator_token)).json()["systems"]]
    assert sid in ids and otro_sid not in ids
    ficha = http_client.get(f"{URL}/{sid}", headers=_auth(collaborator_token)).json()
    assert ficha["can_manage"] is False and len(ficha["environments"]) == 2
    assert http_client.get(f"{URL}/{otro_sid}", headers=_auth(collaborator_token)).status_code == 404


def test_lo_ajeno_es_404(db, http_client, seed_data, admin_token):
    token, _, _ = _sistema_con_entornos(db, http_client, seed_data, admin_token)
    _, ajeno = _cliente_y_proyecto(db, http_client, seed_data)
    ajeno_sid = _crear(http_client, admin_token, ajeno).json()["id"]
    assert http_client.get(f"{URL}/{ajeno_sid}", headers=_auth(token)).status_code == 404
    assert http_client.get(f"{URL}/999999", headers=_auth(token)).status_code == 404

    sufijo = uuid4().hex[:6]
    otra = Organization(name=f"Otra {sufijo}", slug=f"otra-{sufijo}")
    db.add(otra)
    db.flush()
    cliente_otra = Client(organization_id=otra.id, company_name="Cliente de otra organizacion")
    db.add(cliente_otra)
    db.flush()
    proyecto_otra = Project(organization_id=otra.id, client_id=cliente_otra.id, name="Proyecto de otra org")
    db.add(proyecto_otra)
    db.flush()
    s = ClientSystem(organization_id=otra.id, client_id=cliente_otra.id, name="Ajeno", status="en_construccion",
                     support_plan="ninguno")
    db.add(s)
    db.flush()
    e = ClientSystemEnvironment(organization_id=otra.id, system_id=s.id, kind="prod", visible_to_client=True)
    db.add(e)
    db.commit()

    h = _auth(admin_token)
    assert http_client.get(f"{URL}/{s.id}", headers=h).status_code == 404
    assert s.id not in [x["id"] for x in http_client.get(URL, headers=h).json()["systems"]]
    assert http_client.put(f"{URL}/{s.id}", json={"name": "Robado"}, headers=h).status_code == 404
    assert http_client.delete(f"{URL}/{s.id}", headers=h).status_code == 404
    assert _entorno(http_client, admin_token, s.id, kind="dev").status_code == 404
    assert http_client.put(f"{URL}/environments/{e.id}", json={"url": None}, headers=h).status_code == 404
    assert http_client.delete(f"{URL}/environments/{e.id}", headers=h).status_code == 404
    # Ni crear un sistema para un cliente u origen de otra organización.
    cuerpo = {"client_id": cliente_otra.id, "name": "Intruso"}
    assert http_client.post(URL, json=cuerpo, headers=h).status_code == 404
    assert _crear(http_client, admin_token, ajeno, origin_project_id=proyecto_otra.id).status_code == 404


def test_secretos_y_urls_se_rechazan(db, http_client, seed_data, admin_token):
    _, proyecto = _cliente_y_proyecto(db, http_client, seed_data)
    sid = _crear(http_client, admin_token, proyecto).json()["id"]
    for valor in ("sk-abcdefghijklmnop1234", "ghp_" + "a" * 36, "github_pat_" + "B" * 30,
                  "-----BEGIN OPENSSH PRIVATE KEY-----", "AKIA" + "Q" * 16, "xoxb-1234567890-abc",
                  "password: hunter2hunter2"):
        r = _entorno(http_client, admin_token, sid, secrets_location=valor)
        assert r.status_code == 422, (valor, r.text)
    assert _entorno(http_client, admin_token, sid, url="https://admin:clave@tienda.example.com").status_code == 422
    assert _entorno(http_client, admin_token, sid, url="ftp://tienda.example.com").status_code == 422
    assert _entorno(http_client, admin_token, sid, kind="qa").status_code == 422
    assert _crear(http_client, admin_token, proyecto, status="vendido").status_code == 422
    assert _crear(http_client, admin_token, proyecto, support_plan="oro").status_code == 422
    assert db.query(ClientSystemEnvironment).filter(ClientSystemEnvironment.system_id == sid).count() == 0

    # Una ubicación de verdad sí pasa, y un segundo prod del mismo sistema es 409.
    assert _entorno(http_client, admin_token, sid).status_code == 201
    assert _entorno(http_client, admin_token, sid).status_code == 409


def test_proyecto_de_origen_de_otro_cliente_es_422(db, http_client, seed_data, admin_token):
    _, proyecto = _cliente_y_proyecto(db, http_client, seed_data)
    _, otro = _cliente_y_proyecto(db, http_client, seed_data)
    assert _crear(http_client, admin_token, proyecto, origin_project_id=otro.id).status_code == 422


def test_avisos_de_vencimiento(db, http_client, seed_data, admin_token):
    token, proyecto = _cliente_y_proyecto(db, http_client, seed_data)
    pronto = (date.today() + timedelta(days=10)).isoformat()
    lejos = (date.today() + timedelta(days=200)).isoformat()
    sid = _crear(http_client, admin_token, proyecto, warranty_until=pronto, status="en_produccion").json()["id"]
    _entorno(http_client, admin_token, sid, certificate_expires_at=pronto, domain_expires_at=lejos,
             visible_to_client=True)
    _entorno(http_client, admin_token, sid, kind="dev", domain_expires_at=lejos)
    ficha = http_client.get(f"{URL}/{sid}", headers=_auth(admin_token)).json()
    assert ficha["warranty_expiring"] is True
    por_tipo = {e["kind"]: e["expiring_soon"] for e in ficha["environments"]}
    assert por_tipo == {"prod": True, "dev": False}
    assert http_client.get(f"{URL}/{sid}", headers=_auth(token)).json()["warranty_expiring"] is True


def test_solo_se_quita_en_construccion_y_todo_queda_auditado(db, http_client, seed_data, admin_token):
    _, _, sid = _sistema_con_entornos(db, http_client, seed_data, admin_token)
    h = _auth(admin_token)
    env_id = db.query(ClientSystemEnvironment.id).filter(ClientSystemEnvironment.kind == "staging",
                                                         ClientSystemEnvironment.system_id == sid).first()[0]
    r = http_client.put(f"{URL}/environments/{env_id}", json={"visible_to_client": True}, headers=h)
    assert r.status_code == 200 and all(e["visible_to_client"] for e in r.json()["environments"])
    assert http_client.delete(f"{URL}/environments/{env_id}", headers=h).json()["environments"][0]["kind"] == "prod"

    assert http_client.put(f"{URL}/{sid}", json={"status": "en_produccion"}, headers=h).status_code == 200
    assert http_client.delete(f"{URL}/{sid}", headers=h).status_code == 409
    assert http_client.put(f"{URL}/{sid}", json={"status": "en_construccion"}, headers=h).status_code == 200
    r = http_client.delete(f"{URL}/{sid}", headers=h)
    assert r.status_code == 200 and r.json() == {"deleted": sid}
    db.expire_all()
    assert db.get(ClientSystem, sid) is None
    assert db.query(ClientSystemEnvironment).filter(ClientSystemEnvironment.system_id == sid).count() == 0

    acciones = {a for (a,) in db.query(AuditLog.action).filter(
        AuditLog.entity_type == "client_system", AuditLog.entity_id == str(sid))}
    assert {"client_system.created", "client_system.status_updated", "client_system.deleted"} <= acciones
    entornos = {a for (a,) in db.query(AuditLog.action).filter(AuditLog.entity_type == "client_system_environment",
                                                               AuditLog.entity_id == str(env_id))}
    assert {"client_system_environment.created", "client_system_environment.updated",
            "client_system_environment.deleted"} <= entornos
    # La ubicación de las claves no se copia en la auditoría.
    assert not db.query(AuditLog).filter(AuditLog.metadata_json.contains("Gestor de la empresa")).count()
