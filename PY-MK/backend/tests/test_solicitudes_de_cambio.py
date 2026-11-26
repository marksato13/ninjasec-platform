"""35-P-03: solicitudes de cambio como tipo de ticket.

- Un ticket es `incidencia` o `cambio`, con `system_id` opcional.
- El sistema tiene que ser del mismo cliente y organización: si no, 404.
- Flujo: el cliente abre el cambio → el equipo estima → el cliente aprueba o
  rechaza (con motivo) → el admin lo convierte en tarea de un proyecto.
- El equipo no decide por el cliente (403); el cliente no estima ni convierte.
- Una incidencia de un sistema en garantía lo dice: `warranty_until`.
- Todo queda en la auditoría.
"""

from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from app.db.models.audit_log import AuditLog
from app.db.models.client import Client
from app.db.models.client_system import ClientSystem
from app.db.models.organization import Organization
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.project_task import ProjectTask
from app.db.models.support_ticket import SupportTicket
from app.db.models.user import User
from tests.conftest import API
from tests.test_catalog_role_access import _client_token
from tests.test_cliente_no_ve_borradores import _auth, _proyecto_del_cliente

URL = f"{API}/support-tickets"


def _cliente(db, http_client, seed_data, garantia: date | None = None):
    sufijo = f"cam-{uuid4().hex[:6]}"
    token = _client_token(db, http_client, seed_data["org"].id, sufijo)
    proyecto = _proyecto_del_cliente(db, seed_data["org"].id, sufijo)
    sistema = ClientSystem(organization_id=seed_data["org"].id, client_id=proyecto.client_id, name="Tienda",
                           status="en_produccion", support_plan="ninguno", warranty_until=garantia,
                           origin_project_id=proyecto.id)
    db.add(sistema)
    db.commit()
    return token, proyecto, sistema


def _abrir(http_client, token, system_id, kind="cambio", **extra):
    cuerpo = {"title": "Añadir pago con Yape", "description": "En el checkout", "priority": "medium",
              "kind": kind, "system_id": system_id, **extra}
    return http_client.post(f"{URL}/", json=cuerpo, headers=_auth(token))


def _colaborador(db) -> User:
    return db.query(User).filter(User.email == "test-collab@ninjasec.local").one()


def test_flujo_completo_hasta_tareas(db, http_client, seed_data, admin_token, collaborator_token):
    token, proyecto, sistema = _cliente(db, http_client, seed_data)
    r = _abrir(http_client, token, sistema.id)
    assert r.status_code == 201, r.text
    tid = r.json()["id"]
    assert r.json()["kind"] == "cambio" and r.json()["system_id"] == sistema.id

    # Sin estimación no se decide; el colaborador estima.
    assert http_client.post(f"{URL}/{tid}/client-decision", json={"decision": "approved"},
                            headers=_auth(token)).status_code == 409
    r = http_client.post(f"{URL}/{tid}/estimate", json={"hours": 12.5, "note": "Integración y pruebas"},
                         headers=_auth(collaborator_token))
    assert r.status_code == 200, r.text
    assert r.json()["estimate_hours"] == 12.5

    # El cliente ve la estimación y aprueba; no puede decidir dos veces.
    ficha = http_client.get(f"{URL}/{tid}", headers=_auth(token)).json()
    assert ficha["estimate_hours"] == 12.5 and ficha["estimate_note"] == "Integración y pruebas"
    r = http_client.post(f"{URL}/{tid}/client-decision", json={"decision": "approved"}, headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["client_decision"] == "approved" and r.json()["client_decision_at"]
    assert http_client.post(f"{URL}/{tid}/client-decision", json={"decision": "rejected", "note": "Cambié de idea"},
                            headers=_auth(token)).status_code == 409
    # Aprobado, ya no se reestima.
    assert http_client.post(f"{URL}/{tid}/estimate", json={"hours": 3},
                            headers=_auth(admin_token)).status_code == 409

    # El admin lo convierte en tarea de un proyecto nuevo, asignada al colaborador.
    colab = _colaborador(db)
    r = http_client.post(f"{URL}/{tid}/convert", json={"assigned_user_id": colab.id, "project_name": "Pagos Yape"},
                         headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    pid = r.json()["converted_project_id"]
    assert r.json()["status"] == "in_progress"
    db.expire_all()
    nuevo = db.get(Project, pid)
    assert nuevo.client_id == proyecto.client_id and nuevo.name == "Pagos Yape"
    tarea = db.query(ProjectTask).filter(ProjectTask.project_id == pid).one()
    assert tarea.assigned_user_id == colab.id and "12.5 h" in tarea.description
    assert db.query(ProjectMember).filter(ProjectMember.project_id == pid, ProjectMember.user_id == colab.id).count()
    assert http_client.post(f"{URL}/{tid}/convert", json={"assigned_user_id": colab.id},
                            headers=_auth(admin_token)).status_code == 409

    acciones = {a for (a,) in db.query(AuditLog.action).filter(AuditLog.entity_type == "support_tickets",
                                                               AuditLog.entity_id == str(tid))}
    assert {"support_ticket.created", "support_ticket.change_estimated", "support_ticket.change_approved",
            "support_ticket.change_converted"} <= acciones


def test_rechazo_con_motivo_y_reestimacion(db, http_client, seed_data, admin_token):
    token, _, sistema = _cliente(db, http_client, seed_data)
    tid = _abrir(http_client, token, sistema.id).json()["id"]
    http_client.post(f"{URL}/{tid}/estimate", json={"hours": 40}, headers=_auth(admin_token))

    assert http_client.post(f"{URL}/{tid}/client-decision", json={"decision": "rejected"},
                            headers=_auth(token)).status_code == 422
    r = http_client.post(f"{URL}/{tid}/client-decision", json={"decision": "rejected", "note": "Es demasiado"},
                         headers=_auth(token))
    assert r.status_code == 200 and r.json()["client_decision"] == "rejected"
    # Rechazado no se convierte.
    assert http_client.post(f"{URL}/{tid}/convert", json={"assigned_user_id": _colaborador(db).id},
                            headers=_auth(admin_token)).status_code == 409

    # El equipo reestima: la decisión vuelve a abrirse y el cliente puede aprobar.
    r = http_client.post(f"{URL}/{tid}/estimate", json={"hours": 24}, headers=_auth(admin_token))
    assert r.status_code == 200 and r.json()["client_decision"] is None
    r = http_client.post(f"{URL}/{tid}/client-decision", json={"decision": "approved"}, headers=_auth(token))
    assert r.json()["client_decision"] == "approved"
    rechazos = db.query(AuditLog).filter(AuditLog.action == "support_ticket.change_rejected",
                                         AuditLog.entity_id == str(tid)).count()
    assert rechazos == 1


def test_cada_rol_hace_solo_lo_suyo(db, http_client, seed_data, admin_token, collaborator_token):
    token, proyecto, sistema = _cliente(db, http_client, seed_data)
    tid = _abrir(http_client, token, sistema.id).json()["id"]
    # El cliente no estima ni convierte.
    assert http_client.post(f"{URL}/{tid}/estimate", json={"hours": 1}, headers=_auth(token)).status_code == 403
    assert http_client.post(f"{URL}/{tid}/convert", json={"assigned_user_id": 1},
                            headers=_auth(token)).status_code == 403
    http_client.post(f"{URL}/{tid}/estimate", json={"hours": 8}, headers=_auth(admin_token))
    # El equipo no decide por el cliente.
    for t in (admin_token, collaborator_token):
        assert http_client.post(f"{URL}/{tid}/client-decision", json={"decision": "approved"},
                                headers=_auth(t)).status_code == 403
    # El colaborador no convierte.
    http_client.post(f"{URL}/{tid}/client-decision", json={"decision": "approved"}, headers=_auth(token))
    assert http_client.post(f"{URL}/{tid}/convert", json={"assigned_user_id": _colaborador(db).id},
                            headers=_auth(collaborator_token)).status_code == 403
    # Una incidencia no se estima.
    inc = _abrir(http_client, token, sistema.id, kind="incidencia").json()["id"]
    assert http_client.post(f"{URL}/{inc}/estimate", json={"hours": 2},
                            headers=_auth(admin_token)).status_code == 409
    assert _abrir(http_client, token, sistema.id, kind="mejora").status_code == 422
    assert http_client.post(f"{URL}/{tid}/estimate", json={"hours": 0},
                            headers=_auth(admin_token)).status_code == 422


def test_lo_ajeno_es_404(db, http_client, seed_data, admin_token):
    token, proyecto, sistema = _cliente(db, http_client, seed_data)
    otro_token, otro_proyecto, otro_sistema = _cliente(db, http_client, seed_data)

    # El cliente no abre un ticket sobre el sistema de otro cliente.
    assert _abrir(http_client, token, otro_sistema.id).status_code == 404
    # Ni el admin cuelga un sistema de un cliente distinto al del ticket.
    cuerpo = {"client_id": proyecto.client_id, "title": "Mal enlazado", "priority": "low",
              "kind": "cambio", "system_id": otro_sistema.id}
    assert http_client.post(f"{URL}/", json=cuerpo, headers=_auth(admin_token)).status_code == 404

    # Ni decide sobre el cambio de otro.
    tid = _abrir(http_client, token, sistema.id).json()["id"]
    http_client.post(f"{URL}/{tid}/estimate", json={"hours": 5}, headers=_auth(admin_token))
    assert http_client.post(f"{URL}/{tid}/client-decision", json={"decision": "approved"},
                            headers=_auth(otro_token)).status_code == 404
    assert http_client.get(f"{URL}/{tid}", headers=_auth(otro_token)).status_code == 404
    http_client.post(f"{URL}/{tid}/client-decision", json={"decision": "approved"}, headers=_auth(token))

    # Convertir a un proyecto de otro cliente o a un usuario cliente: 404.
    colab = _colaborador(db)
    assert http_client.post(f"{URL}/{tid}/convert", json={"assigned_user_id": colab.id,
                                                          "project_id": otro_proyecto.id},
                            headers=_auth(admin_token)).status_code == 404
    usuario_cliente = db.query(User).filter(User.email.like("portal-catalogos-cam-%")).first()
    assert http_client.post(f"{URL}/{tid}/convert", json={"assigned_user_id": usuario_cliente.id,
                                                          "project_id": proyecto.id},
                            headers=_auth(admin_token)).status_code == 404

    # Otra organización: su sistema, su proyecto y su ticket no existen aquí.
    sufijo = uuid4().hex[:6]
    otra = Organization(name=f"Otra {sufijo}", slug=f"otra-{sufijo}")
    db.add(otra)
    db.flush()
    cliente_otra = Client(organization_id=otra.id, company_name="Cliente ajeno")
    db.add(cliente_otra)
    db.flush()
    sistema_otra = ClientSystem(organization_id=otra.id, client_id=cliente_otra.id, name="Ajeno",
                                status="en_produccion", support_plan="ninguno")
    proyecto_otra = Project(organization_id=otra.id, client_id=cliente_otra.id, name="Ajeno")
    db.add_all([sistema_otra, proyecto_otra])
    db.flush()
    ticket_otra = SupportTicket(organization_id=otra.id, client_id=cliente_otra.id, title="Ajeno",
                                priority="medium", kind="cambio", estimate_hours=3, client_decision="approved")
    db.add(ticket_otra)
    db.commit()
    h = _auth(admin_token)
    cuerpo = {"client_id": cliente_otra.id, "title": "x", "priority": "low", "kind": "cambio",
              "system_id": sistema_otra.id}
    assert http_client.post(f"{URL}/", json=cuerpo, headers=h).status_code == 404
    assert http_client.post(f"{URL}/{ticket_otra.id}/estimate", json={"hours": 1}, headers=h).status_code == 404
    assert http_client.post(f"{URL}/{ticket_otra.id}/convert", json={"assigned_user_id": colab.id},
                            headers=h).status_code == 404
    assert http_client.post(f"{URL}/{tid}/convert", json={"assigned_user_id": colab.id,
                                                          "project_id": proyecto_otra.id},
                            headers=h).status_code == 404
    db.expire_all()
    assert db.get(SupportTicket, tid).converted_project_id is None


def test_incidencia_en_garantia(db, http_client, seed_data):
    pronto = date.today() + timedelta(days=60)
    token, _, sistema = _cliente(db, http_client, seed_data, garantia=pronto)
    inc = _abrir(http_client, token, sistema.id, kind="incidencia").json()
    assert inc["warranty_until"] == pronto.isoformat()
    cambio = _abrir(http_client, token, sistema.id).json()
    assert cambio["warranty_until"] is None  # un cambio no es garantía

    token2, _, vencido = _cliente(db, http_client, seed_data, garantia=date.today() - timedelta(days=1))
    assert _abrir(http_client, token2, vencido.id, kind="incidencia").json()["warranty_until"] is None
    # Sin sistema sigue siendo una incidencia normal.
    sin = http_client.post(f"{URL}/", json={"title": "No carga", "priority": "high"}, headers=_auth(token)).json()
    assert sin["kind"] == "incidencia" and sin["system_id"] is None and sin["warranty_until"] is None
