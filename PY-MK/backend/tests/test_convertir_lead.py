"""Convertir un lead en cliente: una sola vez, completo, auditado y solo para admin.

Antes lo hacia el navegador en dos pasos y el lead no quedaba marcado, asi que pulsar el boton
dos veces creaba dos clientes. Estas pruebas fijan que ya no puede pasar.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.db.models.audit_log import AuditLog
from app.db.models.client import Client
from app.db.models.client_contact import ClientContact
from app.db.models.enums import ClientStatus, LeadStatus
from app.db.models.lead import Lead

API = "/api/v1"


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture
def crear_lead(db, seed_data):
    """Fabrica leads y, al terminar, retira ellos, sus clientes y sus contactos."""
    creados: list[int] = []

    def _crear(**kw) -> Lead:
        datos = dict(contact_name="Lucía Torres", email="lucia@panaderia-demo.pe", phone="+51 999 111 222",
                     company_name="Panadería Torres", interest_area="Firewall", source="website",
                     message="Queremos separar el wifi de visitas.", status=LeadStatus.QUALIFIED)
        datos.update(kw)
        lead = Lead(**datos)
        db.add(lead)
        db.commit()
        creados.append(lead.id)
        return lead

    yield _crear

    db.rollback()
    org_id = seed_data["org"].id
    for lid in creados:
        lead = db.get(Lead, lid)
        if lead is None:
            continue
        cid = lead.converted_client_id
        lead.converted_client_id = None
        db.flush()
        if cid:
            db.query(ClientContact).filter(ClientContact.client_id == cid).delete()
            db.query(Client).filter(Client.id == cid).delete()
        db.delete(lead)
    db.query(AuditLog).filter(AuditLog.organization_id == org_id, AuditLog.action == "lead.converted").delete()
    db.commit()


def _n_clientes(db, seed_data) -> int:
    return db.scalar(select(func.count()).select_from(Client).where(Client.organization_id == seed_data["org"].id))


def test_convierte_el_lead_en_un_cliente_con_su_contacto(http_client, db, admin_token, seed_data, crear_lead):
    lead = crear_lead()
    r = http_client.post(f"{API}/leads/{lead.id}/convert", headers=_auth(admin_token))
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert cuerpo["company_name"] == "Panadería Torres"
    assert cuerpo["lead"]["status"] == "CLOSED_WON"
    assert cuerpo["lead"]["converted_client_id"] == cuerpo["client_id"]

    cliente = db.get(Client, cuerpo["client_id"])
    assert cliente.organization_id == seed_data["org"].id, "El cliente nace en la organizacion del admin"
    assert cliente.commercial_status == ClientStatus.ACTIVE
    contactos = db.scalars(select(ClientContact).where(ClientContact.client_id == cliente.id)).all()
    assert len(contactos) == 1
    c = contactos[0]
    assert (c.name, c.email, c.phone, c.is_primary) == ("Lucía Torres", "lucia@panaderia-demo.pe", "+51 999 111 222", True)
    assert "Firewall" in (cliente.notes or "")


def test_sin_empresa_el_cliente_se_llama_como_el_contacto(http_client, db, admin_token, crear_lead):
    lead = crear_lead(company_name=None, contact_name="Don Pedro Quispe")
    r = http_client.post(f"{API}/leads/{lead.id}/convert", headers=_auth(admin_token))
    assert r.status_code == 201
    assert r.json()["company_name"] == "Don Pedro Quispe"


def test_convertir_dos_veces_no_duplica_el_cliente(http_client, db, admin_token, seed_data, crear_lead):
    """El fallo que existia: dos pulsaciones, dos clientes."""
    lead = crear_lead()
    antes = _n_clientes(db, seed_data)
    primera = http_client.post(f"{API}/leads/{lead.id}/convert", headers=_auth(admin_token))
    segunda = http_client.post(f"{API}/leads/{lead.id}/convert", headers=_auth(admin_token))
    assert primera.status_code == 201
    assert segunda.status_code == 409
    assert _n_clientes(db, seed_data) == antes + 1, "Debe haber un solo cliente nuevo, no dos"


def test_un_lead_perdido_no_se_convierte(http_client, db, admin_token, seed_data, crear_lead):
    lead = crear_lead(status=LeadStatus.CLOSED_LOST)
    antes = _n_clientes(db, seed_data)
    r = http_client.post(f"{API}/leads/{lead.id}/convert", headers=_auth(admin_token))
    assert r.status_code == 409
    assert _n_clientes(db, seed_data) == antes
    db.refresh(lead)
    assert lead.status == LeadStatus.CLOSED_LOST and lead.converted_client_id is None


def test_un_lead_inexistente_da_404(http_client, admin_token):
    assert http_client.post(f"{API}/leads/99999999/convert", headers=_auth(admin_token)).status_code == 404


def test_un_colaborador_no_puede_convertir(http_client, db, collaborator_token, seed_data, crear_lead):
    lead = crear_lead()
    antes = _n_clientes(db, seed_data)
    r = http_client.post(f"{API}/leads/{lead.id}/convert", headers=_auth(collaborator_token))
    assert r.status_code == 403
    assert _n_clientes(db, seed_data) == antes


def test_sin_sesion_da_401(http_client, crear_lead):
    lead = crear_lead()
    assert http_client.post(f"{API}/leads/{lead.id}/convert").status_code == 401


def test_la_conversion_queda_auditada(http_client, db, admin_token, seed_data, crear_lead):
    lead = crear_lead()
    r = http_client.post(f"{API}/leads/{lead.id}/convert", headers=_auth(admin_token))
    assert r.status_code == 201
    fila = db.scalar(select(AuditLog).where(AuditLog.organization_id == seed_data["org"].id,
                                            AuditLog.action == "lead.converted",
                                            AuditLog.entity_id == str(lead.id)))
    assert fila is not None
    assert fila.user_id == seed_data["admin"].id
    assert str(r.json()["client_id"]) in (fila.metadata_json or "")


def test_la_lista_de_leads_dice_cual_ya_esta_convertido(http_client, admin_token, crear_lead):
    lead = crear_lead()
    http_client.post(f"{API}/leads/{lead.id}/convert", headers=_auth(admin_token))
    filas = {x["id"]: x for x in http_client.get(f"{API}/leads/", headers=_auth(admin_token)).json()}
    assert filas[lead.id]["converted_client_id"] is not None
