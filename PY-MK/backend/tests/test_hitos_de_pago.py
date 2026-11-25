"""C3: hitos de pago por proyecto. El admin los gestiona, el cliente dueño los ve.

- Colaborador: 403 por rol (no ve lo que cobra la empresa).
- Proyecto de otro cliente o de otra organización: 404.
- Marcar pagado fija la fecha; volver atrás la borra. Un hito pagado no se quita.
- "Vencido" se calcula; los totales van por moneda. Todo cambio queda auditado.
"""

from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from app.db.models.audit_log import AuditLog
from app.db.models.organization import Organization
from app.db.models.payment_milestone import PaymentMilestone
from app.db.models.project import Project
from tests.conftest import API
from tests.test_catalog_role_access import _client_token
from tests.test_cliente_no_ve_borradores import _auth, _proyecto_del_cliente

URL = f"{API}/payment-milestones"


def _cliente_y_proyecto(db, http_client, seed_data):
    sufijo = f"pago-{uuid4().hex[:6]}"
    token = _client_token(db, http_client, seed_data["org"].id, sufijo)
    return token, _proyecto_del_cliente(db, seed_data["org"].id, sufijo)


def _crear(http_client, admin_token, project_id, **campos):
    cuerpo = {"title": "Anticipo 50 %", "amount": "1500.00", **campos}
    return http_client.post(f"{URL}/projects/{project_id}", json=cuerpo, headers=_auth(admin_token))


def test_el_admin_crea_y_el_cliente_ve_con_totales_y_vencido(db, http_client, seed_data, admin_token):
    token, proyecto = _cliente_y_proyecto(db, http_client, seed_data)
    ayer = (date.today() - timedelta(days=1)).isoformat()

    assert _crear(http_client, admin_token, proyecto.id, due_date=ayer).status_code == 201
    r = _crear(http_client, admin_token, proyecto.id, title="Cierre", amount="1500", status="paid")
    assert r.status_code == 201, r.text
    assert _crear(http_client, admin_token, proyecto.id, title="Licencias", amount="200", currency="USD").status_code == 201

    r = http_client.get(f"{URL}/projects/{proyecto.id}", headers=_auth(token))
    assert r.status_code == 200, r.text
    vista = r.json()
    assert vista["can_manage"] is False
    por_titulo = {h["title"]: h for h in vista["milestones"]}
    assert por_titulo["Anticipo 50 %"]["overdue"] is True
    assert por_titulo["Cierre"]["overdue"] is False and por_titulo["Cierre"]["paid_at"] is not None
    totales = {t["currency"]: t for t in vista["totals"]}
    assert float(totales["PEN"]["total"]) == 3000 and float(totales["PEN"]["paid"]) == 1500
    assert float(totales["USD"]["pending"]) == 200


def test_el_cliente_no_puede_crear_ni_editar(db, http_client, seed_data, admin_token):
    token, proyecto = _cliente_y_proyecto(db, http_client, seed_data)
    assert _crear(http_client, token, proyecto.id).status_code == 403
    hito_id = _crear(http_client, admin_token, proyecto.id).json()["milestones"][0]["id"]
    assert http_client.put(f"{URL}/{hito_id}", json={"status": "paid"}, headers=_auth(token)).status_code == 403
    assert http_client.delete(f"{URL}/{hito_id}", headers=_auth(token)).status_code == 403
    assert db.get(PaymentMilestone, hito_id).status == "pending"


def test_el_colaborador_no_ve_pagos(db, http_client, seed_data, admin_token, collaborator_token):
    _, proyecto = _cliente_y_proyecto(db, http_client, seed_data)
    _crear(http_client, admin_token, proyecto.id)
    assert http_client.get(f"{URL}/projects/{proyecto.id}", headers=_auth(collaborator_token)).status_code == 403


def test_proyecto_de_otro_cliente_u_otra_organizacion_es_404(db, http_client, seed_data, admin_token):
    token, _ = _cliente_y_proyecto(db, http_client, seed_data)
    _, ajeno = _cliente_y_proyecto(db, http_client, seed_data)
    _crear(http_client, admin_token, ajeno.id)
    assert http_client.get(f"{URL}/projects/{ajeno.id}", headers=_auth(token)).status_code == 404
    assert http_client.get(f"{URL}/projects/999999", headers=_auth(token)).status_code == 404

    sufijo = uuid4().hex[:6]
    otra = Organization(name=f"Otra {sufijo}", slug=f"otra-{sufijo}")
    db.add(otra)
    db.flush()
    de_otra = Project(organization_id=otra.id, name="Proyecto de otra organizacion")
    db.add(de_otra)
    db.flush()
    hito = PaymentMilestone(organization_id=otra.id, project_id=de_otra.id, title="Ajeno", amount=10,
                            currency="PEN", status="pending")
    db.add(hito)
    db.commit()
    assert http_client.get(f"{URL}/projects/{de_otra.id}", headers=_auth(admin_token)).status_code == 404
    assert _crear(http_client, admin_token, de_otra.id).status_code == 404
    r = http_client.put(f"{URL}/{hito.id}", json={"status": "paid"}, headers=_auth(admin_token))
    assert r.status_code == 404
    assert http_client.delete(f"{URL}/{hito.id}", headers=_auth(admin_token)).status_code == 404


def test_pagado_fija_fecha_volver_la_borra_y_no_se_quita(db, http_client, seed_data, admin_token):
    _, proyecto = _cliente_y_proyecto(db, http_client, seed_data)
    hito_id = _crear(http_client, admin_token, proyecto.id).json()["milestones"][0]["id"]

    r = http_client.put(f"{URL}/{hito_id}", json={"status": "paid"}, headers=_auth(admin_token))
    assert r.status_code == 200 and r.json()["milestones"][0]["paid_at"] is not None
    assert http_client.delete(f"{URL}/{hito_id}", headers=_auth(admin_token)).status_code == 409

    r = http_client.put(f"{URL}/{hito_id}", json={"status": "invoiced"}, headers=_auth(admin_token))
    assert r.json()["milestones"][0]["paid_at"] is None
    assert http_client.delete(f"{URL}/{hito_id}", headers=_auth(admin_token)).status_code == 200
    assert db.get(PaymentMilestone, hito_id) is None

    acciones = {a for (a,) in db.query(AuditLog.action).filter(
        AuditLog.entity_type == "payment_milestone", AuditLog.entity_id == str(hito_id))}
    assert {"payment_milestone.created", "payment_milestone.status_updated",
            "payment_milestone.deleted"} <= acciones


def test_validaciones(db, http_client, seed_data, admin_token):
    _, proyecto = _cliente_y_proyecto(db, http_client, seed_data)
    assert _crear(http_client, admin_token, proyecto.id, amount="0").status_code == 422
    assert _crear(http_client, admin_token, proyecto.id, amount="-5").status_code == 422
    assert _crear(http_client, admin_token, proyecto.id, currency="EUR").status_code == 422
    assert _crear(http_client, admin_token, proyecto.id, status="refunded").status_code == 422
    assert _crear(http_client, admin_token, proyecto.id, title="x").status_code == 422
