"""35-P-05: pruebas de aceptación (UAT) por proyecto.

- El equipo (admin o colaborador del proyecto) escribe los casos; el cliente los marca.
- Observar exige nota (≥5); un caso aprobado ya no cambia ni se borra.
- El equipo no decide por el cliente (403); el cliente no escribe casos (403).
- Lo ajeno (otro proyecto, otro cliente, otra organización) es 404.
- El cliente no recibe quién del equipo escribió o decidió.
- Todos aprobados → `ready_for_signoff`.
- Todo queda en la auditoría.
"""

from __future__ import annotations

from uuid import uuid4

from app.db.models.acceptance_case import AcceptanceCase
from app.db.models.audit_log import AuditLog
from app.db.models.client import Client
from app.db.models.organization import Organization
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.user import User
from tests.conftest import API
from tests.test_catalog_role_access import _client_token
from tests.test_cliente_no_ve_borradores import _auth, _proyecto_del_cliente

URL = f"{API}/acceptance-cases"
CASO = {"title": "Pagar con tarjeta", "steps": "Añadir un producto y pagar", "expected": "Llega el correo de compra"}


def _cliente(db, http_client, seed_data):
    sufijo = f"uat-{uuid4().hex[:6]}"
    token = _client_token(db, http_client, seed_data["org"].id, sufijo)
    proyecto = _proyecto_del_cliente(db, seed_data["org"].id, sufijo)
    return token, proyecto


def _colaborador(db) -> User:
    return db.query(User).filter(User.email == "test-collab@ninjasec.local").one()


def _miembro(db, proyecto: Project) -> None:
    db.add(ProjectMember(project_id=proyecto.id, user_id=_colaborador(db).id))
    db.commit()


def _crear(http_client, token, project_id, **extra):
    return http_client.post(f"{URL}/projects/{project_id}", json={**CASO, **extra}, headers=_auth(token))


def test_flujo_hasta_listo_para_el_acta(db, http_client, seed_data, admin_token, collaborator_token):
    token, proyecto = _cliente(db, http_client, seed_data)
    _miembro(db, proyecto)

    r = _crear(http_client, admin_token, proyecto.id)
    assert r.status_code == 201, r.text
    r = _crear(http_client, collaborator_token, proyecto.id, title="Ver el pedido")
    assert r.status_code == 201, r.text
    vista = r.json()
    assert vista["summary"] == {"total": 2, "pendiente": 2, "aprobado": 0, "observado": 0, "ready_for_signoff": False}
    uno, dos = (c["id"] for c in vista["cases"])
    assert [c["position"] for c in vista["cases"]] == [1, 2]

    # Observar sin nota no vale; con nota sí.
    assert http_client.post(f"{URL}/{uno}/decision", json={"decision": "observado", "note": "no"},
                            headers=_auth(token)).status_code == 422
    r = http_client.post(f"{URL}/{uno}/decision", json={"decision": "observado", "note": "No llegó el correo"},
                         headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["summary"]["observado"] == 1

    # El equipo corrige lo que se comprueba: vuelve a pendiente.
    r = http_client.put(f"{URL}/{uno}", json={"expected": "Llega el correo en menos de 1 minuto"},
                        headers=_auth(collaborator_token))
    assert r.status_code == 200, r.text
    caso = next(c for c in r.json()["cases"] if c["id"] == uno)
    assert caso["status"] == "pendiente" and caso["decided_at"] is None

    for cid in (uno, dos):
        r = http_client.post(f"{URL}/{cid}/decision", json={"decision": "aprobado"}, headers=_auth(token))
        assert r.status_code == 200, r.text
    assert r.json()["summary"]["ready_for_signoff"] is True

    # Aprobado es evidencia: no se decide otra vez, no se cambia la prueba, no se borra.
    assert http_client.post(f"{URL}/{uno}/decision", json={"decision": "observado", "note": "Cambié de idea"},
                            headers=_auth(token)).status_code == 409
    assert http_client.put(f"{URL}/{uno}", json={"steps": "Otra cosa distinta"},
                           headers=_auth(admin_token)).status_code == 409
    assert http_client.delete(f"{URL}/{uno}", headers=_auth(admin_token)).status_code == 409


def test_cada_rol_hace_solo_lo_suyo(db, http_client, seed_data, admin_token, collaborator_token):
    token, proyecto = _cliente(db, http_client, seed_data)
    _miembro(db, proyecto)
    cid = _crear(http_client, admin_token, proyecto.id).json()["cases"][0]["id"]

    # El cliente no escribe, no corrige, no borra.
    assert _crear(http_client, token, proyecto.id).status_code == 403
    assert http_client.put(f"{URL}/{cid}", json={"title": "Otro título"}, headers=_auth(token)).status_code == 403
    assert http_client.delete(f"{URL}/{cid}", headers=_auth(token)).status_code == 403
    # El equipo no decide por el cliente; el colaborador no borra.
    for t in (admin_token, collaborator_token):
        assert http_client.post(f"{URL}/{cid}/decision", json={"decision": "aprobado"},
                                headers=_auth(t)).status_code == 403
    assert http_client.delete(f"{URL}/{cid}", headers=_auth(collaborator_token)).status_code == 403
    # El admin borra uno pendiente.
    r = http_client.delete(f"{URL}/{cid}", headers=_auth(admin_token))
    assert r.status_code == 200 and r.json()["summary"]["total"] == 0


def test_el_colaborador_fuera_del_proyecto_no_lo_ve(db, http_client, seed_data, admin_token, collaborator_token):
    _, proyecto = _cliente(db, http_client, seed_data)
    cid = _crear(http_client, admin_token, proyecto.id).json()["cases"][0]["id"]
    assert http_client.get(f"{URL}/projects/{proyecto.id}", headers=_auth(collaborator_token)).status_code == 404
    assert _crear(http_client, collaborator_token, proyecto.id).status_code == 404
    assert http_client.put(f"{URL}/{cid}", json={"title": "Infiltrado"},
                           headers=_auth(collaborator_token)).status_code == 404


def test_el_cliente_ve_solo_lo_suyo_y_sin_lo_interno(db, http_client, seed_data, admin_token):
    token, proyecto = _cliente(db, http_client, seed_data)
    _, ajeno = _cliente(db, http_client, seed_data)
    _crear(http_client, admin_token, proyecto.id)
    ajeno_cid = _crear(http_client, admin_token, ajeno.id).json()["cases"][0]["id"]

    r = http_client.get(f"{URL}/projects/{proyecto.id}", headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["can_decide"] is True and r.json()["can_manage"] is False
    caso = r.json()["cases"][0]
    for interno in ("created_by", "decided_by", "created_at", "updated_at"):
        assert interno not in caso, interno

    assert http_client.get(f"{URL}/projects/{ajeno.id}", headers=_auth(token)).status_code == 404
    assert http_client.post(f"{URL}/{ajeno_cid}/decision", json={"decision": "aprobado"},
                            headers=_auth(token)).status_code == 404


def test_lo_de_otra_organizacion_es_404(db, http_client, admin_token):
    sufijo = uuid4().hex[:6]
    otra = Organization(name=f"Otra {sufijo}", slug=f"otra-{sufijo}")
    db.add(otra)
    db.flush()
    cliente = Client(organization_id=otra.id, company_name="Cliente de otra organización")
    db.add(cliente)
    db.flush()
    proyecto = Project(organization_id=otra.id, client_id=cliente.id, name="Proyecto ajeno")
    db.add(proyecto)
    db.flush()
    caso = AcceptanceCase(organization_id=otra.id, project_id=proyecto.id, position=1, title="Ajeno",
                          steps="Pasos", expected="Resultado", status="pendiente")
    db.add(caso)
    db.commit()

    h = _auth(admin_token)
    assert http_client.get(f"{URL}/projects/{proyecto.id}", headers=h).status_code == 404
    assert _crear(http_client, admin_token, proyecto.id).status_code == 404
    assert http_client.put(f"{URL}/{caso.id}", json={"title": "Infiltrado"}, headers=h).status_code == 404
    assert http_client.delete(f"{URL}/{caso.id}", headers=h).status_code == 404
    assert http_client.get(f"{URL}/projects/999999", headers=h).status_code == 404


def test_sin_secretos_en_los_textos(db, http_client, seed_data, admin_token):
    _, proyecto = _cliente(db, http_client, seed_data)
    clave = "gh" + "p_" + "A" * 36  # se arma al ejecutar: no queda una clave literal en el repositorio
    r = _crear(http_client, admin_token, proyecto.id, steps=f"Entrar con el token {clave}")
    assert r.status_code == 422, r.text


def test_todo_queda_en_la_auditoria(db, http_client, seed_data, admin_token):
    token, proyecto = _cliente(db, http_client, seed_data)
    cid = _crear(http_client, admin_token, proyecto.id).json()["cases"][0]["id"]
    http_client.put(f"{URL}/{cid}", json={"title": "Pagar con Yape"}, headers=_auth(admin_token))
    http_client.post(f"{URL}/{cid}/decision", json={"decision": "observado", "note": "No aparece Yape"},
                     headers=_auth(token))
    acciones = {a.action for a in db.query(AuditLog).filter(AuditLog.entity_type == "acceptance_case",
                                                              AuditLog.entity_id == str(cid))}
    assert {"acceptance_case.created", "acceptance_case.updated", "acceptance_case.observado"} <= acciones
