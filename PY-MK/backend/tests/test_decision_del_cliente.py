"""C1: el cliente aprueba un entregable o pide cambios.

- Solo el cliente dueño del proyecto y solo sobre documentos que ya puede ver.
- Lo ajeno, lo interno y los borradores son 404 (no se confirma que existan).
- Pedir cambios exige un motivo; una aprobación es definitiva (409) hasta que el
  equipo sube una versión nueva, que reabre la decisión.
- Cada decisión queda en la auditoría.
"""

from __future__ import annotations

from uuid import uuid4

from app.db.models.audit_log import AuditLog
from app.db.models.enums import DocStatus, DocVisibility
from app.db.models.project_doc import ProjectDoc
from tests.conftest import API
from tests.test_catalog_role_access import _client_token
from tests.test_cliente_no_ve_borradores import _auth, _doc, _proyecto_del_cliente


def _cliente_con_doc(db, http_client, seed_data, estado=DocStatus.ACTIVE):
    sufijo = f"dec-{uuid4().hex[:6]}"
    token = _client_token(db, http_client, seed_data["org"].id, sufijo)
    proyecto = _proyecto_del_cliente(db, seed_data["org"].id, sufijo)
    return token, proyecto, _doc(db, proyecto.id, estado)


def _decidir(http_client, token, doc_id, **cuerpo):
    return http_client.post(f"{API}/project-docs/{doc_id}/client-decision", json=cuerpo, headers=_auth(token))


def test_el_cliente_aprueba_su_entregable_y_queda_auditado(db, http_client, seed_data):
    token, proyecto, doc = _cliente_con_doc(db, http_client, seed_data)

    r = _decidir(http_client, token, doc.id, decision="approved")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["client_decision"] == "approved"
    assert cuerpo["client_decision_at"] is not None
    assert cuerpo["client_decision_by"] is not None

    auditado = db.query(AuditLog).filter(
        AuditLog.action == "project_doc.client_approved", AuditLog.entity_id == str(doc.id)
    ).count()
    assert auditado == 1


def test_pedir_cambios_exige_motivo(db, http_client, seed_data):
    token, _, doc = _cliente_con_doc(db, http_client, seed_data)

    assert _decidir(http_client, token, doc.id, decision="changes_requested").status_code == 422
    assert _decidir(http_client, token, doc.id, decision="changes_requested", note="  ").status_code == 422

    r = _decidir(http_client, token, doc.id, decision="changes_requested", note="Falta el diagrama de la sede 2")
    assert r.status_code == 200, r.text
    assert r.json()["client_decision"] == "changes_requested"
    assert r.json()["client_decision_note"] == "Falta el diagrama de la sede 2"


def test_una_aprobacion_no_se_cambia_y_una_version_nueva_la_reabre(db, http_client, seed_data, admin_token):
    token, _, doc = _cliente_con_doc(db, http_client, seed_data)
    assert _decidir(http_client, token, doc.id, decision="approved").status_code == 200

    r = _decidir(http_client, token, doc.id, decision="changes_requested", note="Lo pienso mejor")
    assert r.status_code == 409

    # El equipo corrige el documento: la decision anterior ya no vale.
    r = http_client.put(f"{API}/project-docs/{doc.id}", json={"summary": "Version 2"}, headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    assert r.json()["client_decision"] is None

    assert _decidir(http_client, token, doc.id, decision="approved").status_code == 200


def test_cambiar_solo_la_visibilidad_no_reabre_la_decision(db, http_client, seed_data, admin_token):
    token, _, doc = _cliente_con_doc(db, http_client, seed_data)
    assert _decidir(http_client, token, doc.id, decision="approved").status_code == 200

    r = http_client.put(f"{API}/project-docs/{doc.id}", json={"enabled": True}, headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    assert r.json()["client_decision"] == "approved"


def test_lo_ajeno_interno_o_en_borrador_es_404(db, http_client, seed_data):
    token, proyecto, _ = _cliente_con_doc(db, http_client, seed_data)
    borrador = _doc(db, proyecto.id, DocStatus.DRAFT)

    interno = _doc(db, proyecto.id, DocStatus.ACTIVE)
    db.get(ProjectDoc, interno.id).visibility = DocVisibility.INTERNAL
    db.commit()

    _, _, ajeno = _cliente_con_doc(db, http_client, seed_data)

    for doc_id in (borrador.id, interno.id, ajeno.id, 999_999):
        r = _decidir(http_client, token, doc_id, decision="approved")
        assert r.status_code == 404, (doc_id, r.text)
    assert db.get(ProjectDoc, ajeno.id).client_decision is None


def test_el_equipo_no_puede_decidir_por_el_cliente(db, http_client, seed_data, admin_token, collaborator_token):
    _, _, doc = _cliente_con_doc(db, http_client, seed_data)
    for token in (admin_token, collaborator_token):
        assert _decidir(http_client, token, doc.id, decision="approved").status_code == 403
    assert db.get(ProjectDoc, doc.id).client_decision is None


def test_el_colaborador_ajeno_al_proyecto_recibe_404_al_editar(db, http_client, seed_data, collaborator_token):
    _, _, doc = _cliente_con_doc(db, http_client, seed_data)
    r = http_client.put(f"{API}/project-docs/{doc.id}", json={"summary": "x"}, headers=_auth(collaborator_token))
    assert r.status_code == 404
