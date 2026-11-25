"""35-P-02: registro de despliegues.

- Admin y colaborador del proyecto registran; el cliente solo lee.
- El cliente ve solo despliegues a prod que llegaron (ok o revertido), sin checklist.
- Lo ajeno (otro cliente, otra organización, inexistente): 404.
- El entorno debe ser del sistema; un ok a prod exige respaldo y prueba de humo.
- Un ok a prod publica "Versión X publicada" en la bitácora, una sola vez.
- Todo se audita.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from app.core.time_utils import utcnow
from app.db.models.audit_log import AuditLog
from app.db.models.client import Client
from app.db.models.client_system import ClientSystem, ClientSystemEnvironment
from app.db.models.client_system_deployment import ClientSystemDeployment
from app.db.models.organization import Organization
from app.db.models.project_member import ProjectMember
from app.db.models.project_tracking import ProjectUpdate
from app.db.models.user import User
from tests.conftest import API
from tests.test_cliente_no_ve_borradores import _auth
from tests.test_sistemas_del_cliente import _sistema_con_entornos

URL = f"{API}/deployments"
CHECK_OK = {"backup_done": True, "smoke_test_passed": True, "rollback_plan_written": True,
            "rollback_plan": "Volver a la etiqueta anterior y restaurar el respaldo"}


def _entornos(db, sid):
    return {k: i for (i, k) in db.query(ClientSystemEnvironment.id, ClientSystemEnvironment.kind)
            .filter(ClientSystemEnvironment.system_id == sid)}


def _registrar(http_client, token, sid, env_id, **campos):
    cuerpo = {"system_id": sid, "environment_id": env_id, "version": "v1.2.0",
              "summary": "Nuevo carrito de compras", **CHECK_OK, **campos}
    return http_client.post(URL, json=cuerpo, headers=_auth(token))


def _base(db, http_client, seed_data, admin_token):
    token, proyecto, sid = _sistema_con_entornos(db, http_client, seed_data, admin_token)
    return token, proyecto, sid, _entornos(db, sid)


def test_ok_a_prod_publica_en_la_bitacora_una_vez(db, http_client, seed_data, admin_token):
    _, proyecto, sid, env = _base(db, http_client, seed_data, admin_token)
    r = _registrar(http_client, admin_token, sid, env["prod"])
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["environment_kind"] == "prod" and d["project_id"] == proyecto.id and d["published_update_id"]
    u = db.get(ProjectUpdate, d["published_update_id"])
    assert u.title == "Versión v1.2.0 publicada" and u.visible_to_client and u.project_id == proyecto.id
    assert u.link_url == "https://tienda.example.com"  # el entorno prod es visible para el cliente

    # Editar no vuelve a publicar.
    r = http_client.put(f"{URL}/{d['id']}", json={"summary": "Nuevo carrito y cupones"}, headers=_auth(admin_token))
    assert r.status_code == 200 and r.json()["published_update_id"] == d["published_update_id"]
    assert db.query(ProjectUpdate).filter(ProjectUpdate.project_id == proyecto.id,
                                          ProjectUpdate.title.like("Versión%")).count() == 1

    # A staging no publica nada.
    r = _registrar(http_client, admin_token, sid, env["staging"], version="v1.3.0-rc1",
                   backup_done=False, smoke_test_passed=False)
    assert r.status_code == 201 and r.json()["published_update_id"] is None


def test_prod_ok_exige_respaldo_y_prueba_de_humo(db, http_client, seed_data, admin_token):
    _, _, sid, env = _base(db, http_client, seed_data, admin_token)
    r = _registrar(http_client, admin_token, sid, env["prod"], backup_done=False, smoke_test_passed=False)
    assert r.status_code == 422 and "respaldo y prueba de humo" in r.text
    assert _registrar(http_client, admin_token, sid, env["prod"], smoke_test_passed=False).status_code == 422
    # Un fallido sí se registra sin checklist: es justo lo que hay que dejar escrito.
    r = _registrar(http_client, admin_token, sid, env["prod"], result="fallido", backup_done=False,
                   smoke_test_passed=False)
    assert r.status_code == 201 and r.json()["published_update_id"] is None
    # ...pero no se puede pasar a ok sin completar el checklist.
    did = r.json()["id"]
    assert http_client.put(f"{URL}/{did}", json={"result": "ok"}, headers=_auth(admin_token)).status_code == 422
    r = http_client.put(f"{URL}/{did}", json={"result": "ok", "backup_done": True, "smoke_test_passed": True},
                        headers=_auth(admin_token))
    assert r.status_code == 200 and r.json()["published_update_id"]
    assert db.query(ClientSystemDeployment).filter(ClientSystemDeployment.system_id == sid).count() == 1


def test_validaciones(db, http_client, seed_data, admin_token):
    _, _, sid, env = _base(db, http_client, seed_data, admin_token)
    _, _, otro_sid, otro_env = _base(db, http_client, seed_data, admin_token)
    assert _registrar(http_client, admin_token, sid, otro_env["prod"]).status_code == 422  # entorno de otro sistema
    assert _registrar(http_client, admin_token, sid, 999999).status_code == 404
    assert _registrar(http_client, admin_token, sid, env["prod"], result="exito").status_code == 422
    assert _registrar(http_client, admin_token, sid, env["prod"], version="v1 2").status_code == 422
    futuro = (utcnow() + timedelta(days=2)).isoformat()
    assert _registrar(http_client, admin_token, sid, env["prod"], deployed_at=futuro).status_code == 422
    # Secretos armados en ejecución para no dejar nada con forma de clave en el repo.
    for valor in ("sk-" + "a" * 20, "gh" + "p_" + "b" * 36, "AK" + "IA" + "Q" * 16, "password: " + "x" * 10):
        assert _registrar(http_client, admin_token, sid, env["prod"], rollback_plan=valor).status_code == 422, valor
        assert _registrar(http_client, admin_token, sid, env["prod"], summary="Cambio " + valor).status_code == 422
    assert db.query(ClientSystemDeployment).filter(ClientSystemDeployment.system_id.in_([sid, otro_sid])).count() == 0


def test_el_cliente_ve_solo_prod_que_llego_y_sin_lo_interno(db, http_client, seed_data, admin_token):
    token, _, sid, env = _base(db, http_client, seed_data, admin_token)
    ok = _registrar(http_client, admin_token, sid, env["prod"]).json()["id"]
    fallido = _registrar(http_client, admin_token, sid, env["prod"], version="v1.2.1", result="fallido").json()["id"]
    staging = _registrar(http_client, admin_token, sid, env["staging"], version="v1.3.0").json()["id"]
    _, _, ajeno_sid, ajeno_env = _base(db, http_client, seed_data, admin_token)
    ajeno = _registrar(http_client, admin_token, ajeno_sid, ajeno_env["prod"]).json()["id"]

    r = http_client.get(URL, headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["can_register"] is False
    assert [d["id"] for d in r.json()["deployments"]] == [ok]
    d = http_client.get(f"{URL}/{ok}", headers=_auth(token)).json()
    assert set(d) == {"id", "system_id", "system_name", "environment_kind", "version", "summary",
                      "deployed_at", "result"}
    assert "Volver a la etiqueta" not in r.text
    for oculto in (fallido, staging, ajeno, 999999):
        assert http_client.get(f"{URL}/{oculto}", headers=_auth(token)).status_code == 404

    # Revertido sigue a la vista: el cliente vivió esa versión.
    assert http_client.put(f"{URL}/{ok}", json={"result": "revertido"}, headers=_auth(admin_token)).status_code == 200
    assert http_client.get(f"{URL}/{ok}", headers=_auth(token)).json()["result"] == "revertido"


def test_roles(db, http_client, seed_data, admin_token, collaborator_token):
    token, proyecto, sid, env = _base(db, http_client, seed_data, admin_token)
    did = _registrar(http_client, admin_token, sid, env["staging"]).json()["id"]

    # Cliente: no registra, no edita, no borra.
    assert _registrar(http_client, token, sid, env["staging"]).status_code == 403
    assert http_client.put(f"{URL}/{did}", json={"result": "fallido"}, headers=_auth(token)).status_code == 403
    assert http_client.delete(f"{URL}/{did}", headers=_auth(token)).status_code == 403

    # Colaborador fuera del proyecto: no ve el sistema, así que es 404.
    assert _registrar(http_client, collaborator_token, sid, env["staging"]).status_code == 404
    assert http_client.get(f"{URL}/{did}", headers=_auth(collaborator_token)).status_code == 404

    colab = db.query(User).filter(User.email == "test-collab@ninjasec.local").one()
    db.add(ProjectMember(project_id=proyecto.id, user_id=colab.id))
    db.commit()

    r = _registrar(http_client, collaborator_token, sid, env["staging"], version="v2.0.0")
    assert r.status_code == 201 and r.json()["deployed_by"] == colab.id and r.json()["can_edit"] is True
    propio = r.json()["id"]
    assert http_client.put(f"{URL}/{propio}", json={"result": "fallido"},
                           headers=_auth(collaborator_token)).status_code == 200
    # Lo del admin lo ve pero no lo corrige; y borrar es solo del admin.
    assert http_client.get(f"{URL}/{did}", headers=_auth(collaborator_token)).json()["can_edit"] is False
    assert http_client.put(f"{URL}/{did}", json={"result": "fallido"},
                           headers=_auth(collaborator_token)).status_code == 403
    assert http_client.delete(f"{URL}/{propio}", headers=_auth(collaborator_token)).status_code == 403


def test_otra_organizacion_es_404(db, http_client, seed_data, admin_token):
    sufijo = uuid4().hex[:6]
    otra = Organization(name=f"Otra {sufijo}", slug=f"otra-{sufijo}")
    db.add(otra)
    db.flush()
    cliente = Client(organization_id=otra.id, company_name="Cliente de otra organizacion")
    db.add(cliente)
    db.flush()
    s = ClientSystem(organization_id=otra.id, client_id=cliente.id, name="Ajeno", status="en_produccion",
                     support_plan="ninguno")
    db.add(s)
    db.flush()
    e = ClientSystemEnvironment(organization_id=otra.id, system_id=s.id, kind="prod", visible_to_client=True)
    db.add(e)
    db.flush()
    d = ClientSystemDeployment(organization_id=otra.id, system_id=s.id, environment_id=e.id,
                               environment_kind="prod", version="v9", summary="Ajeno", result="ok",
                               backup_done=True, smoke_test_passed=True)
    db.add(d)
    db.commit()

    h = _auth(admin_token)
    assert http_client.get(f"{URL}/{d.id}", headers=h).status_code == 404
    assert d.id not in [x["id"] for x in http_client.get(URL, headers=h).json()["deployments"]]
    assert http_client.put(f"{URL}/{d.id}", json={"result": "fallido"}, headers=h).status_code == 404
    assert http_client.delete(f"{URL}/{d.id}", headers=h).status_code == 404
    assert _registrar(http_client, admin_token, s.id, e.id).status_code == 404
    # Ni colgar un despliegue propio de un entorno de otra organización.
    _, _, sid, _ = _base(db, http_client, seed_data, admin_token)
    assert _registrar(http_client, admin_token, sid, e.id).status_code == 404


def test_todo_queda_auditado_y_el_entorno_quitado_no_borra_la_historia(db, http_client, seed_data, admin_token):
    _, _, sid, env = _base(db, http_client, seed_data, admin_token)
    h = _auth(admin_token)
    did = _registrar(http_client, admin_token, sid, env["staging"]).json()["id"]
    assert http_client.put(f"{URL}/{did}", json={"result": "revertido"}, headers=h).status_code == 200
    otro = _registrar(http_client, admin_token, sid, env["staging"], version="v1.2.1").json()["id"]
    r = http_client.delete(f"{URL}/{otro}", headers=h)
    assert r.status_code == 200 and r.json() == {"deleted": otro}

    acciones = {a for (a,) in db.query(AuditLog.action).filter(
        AuditLog.entity_type == "client_system_deployment", AuditLog.entity_id.in_([str(did), str(otro)]))}
    assert {"client_system_deployment.created", "client_system_deployment.result_updated",
            "client_system_deployment.deleted"} <= acciones
    assert not db.query(AuditLog).filter(AuditLog.entity_type == "client_system_deployment",
                                         AuditLog.metadata_json.contains("Volver a la etiqueta")).count()

    # Quitar el entorno deja el despliegue, con su tipo copiado.
    assert http_client.delete(f"{API}/client-systems/environments/{env['staging']}", headers=h).status_code == 200
    db.expire_all()
    d = db.get(ClientSystemDeployment, did)
    if d is not None:  # SQLite sin claves foráneas activas no aplica SET NULL; Postgres sí
        r = http_client.get(f"{URL}/{did}", headers=h)
        assert r.status_code == 200 and r.json()["environment_kind"] == "staging"
