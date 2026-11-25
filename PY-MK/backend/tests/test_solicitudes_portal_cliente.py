"""Solicitudes de servicio: el portal del cliente no confia en un correo escrito por un anonimo.

Auditoria de seguridad del 2026-11-25:

- A3: el listado del cliente filtraba por `requester_email`, un dato que
  escribe cualquiera en el formulario publico. Un anonimo podia plantar una
  solicitud con un mensaje de phishing en el portal de un cliente real.
- A4: `PATCH /services/requests/{id}` cambiaba solicitudes de otra
  organizacion.
"""

from uuid import uuid4

from app.core.security import hash_password
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.enums import RoleCode, ServiceRequestStatus, UserStatus
from app.db.models.organization import Organization
from app.db.models.role import Role
from app.db.models.service import Service
from app.db.models.service_request import ServiceRequest
from app.db.models.user import User
from tests.conftest import API


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _servicio(db, org_id: int) -> Service:
    sufijo = uuid4().hex[:6]
    servicio = Service(organization_id=org_id, title=f"Auditoria {sufijo}", slug=f"auditoria-{sufijo}")
    db.add(servicio)
    db.commit()
    return servicio


def _cliente_con_sesion(db, http_client, org_id: int) -> tuple[Client, str, str]:
    sufijo = uuid4().hex[:8]
    rol = db.query(Role).filter(Role.code == RoleCode.CLIENT.value).first()
    if rol is None:
        rol = Role(code=RoleCode.CLIENT.value, name="Client")
        db.add(rol)
        db.flush()
    cliente = Client(organization_id=org_id, company_name=f"Cliente {sufijo}")
    usuario = User(
        organization_id=org_id,
        role_id=rol.id,
        full_name=f"Gerente {sufijo}",
        email=f"gerente-{sufijo}@example.com",
        password_hash=hash_password("clave-cliente-123"),
        role_code=RoleCode.CLIENT,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add_all([cliente, usuario])
    db.flush()
    db.add(ClientProfile(client_id=cliente.id, user_id=usuario.id))
    db.commit()
    r = http_client.post(f"{API}/auth/login", json={"email": usuario.email, "password": "clave-cliente-123"})
    assert r.status_code == 200, r.text
    return cliente, usuario.email, r.json()["access_token"]


def test_un_anonimo_no_puede_plantar_una_solicitud_en_el_portal_de_un_cliente(http_client, db, seed_data):
    org_id = seed_data["org"].id
    servicio = _servicio(db, org_id)
    cliente, correo, token = _cliente_con_sesion(db, http_client, org_id)

    r = http_client.post(
        f"{API}/services/requests",
        json={
            "service_id": servicio.id,
            "client_id": cliente.id,
            "requester_name": "Soporte",
            "requester_email": correo,
            "message": "Verifique su pago en https://ejemplo.invalid",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["client_id"] is None, "Un anonimo eligio el client_id de la solicitud"

    visibles = http_client.get(f"{API}/services/requests", headers=_auth(token)).json()
    assert r.json()["id"] not in {s["id"] for s in visibles}, (
        "La solicitud de un anonimo aparece en el portal del cliente"
    )


def test_la_solicitud_del_cliente_con_sesion_queda_en_su_portal(http_client, db, seed_data):
    org_id = seed_data["org"].id
    servicio = _servicio(db, org_id)
    cliente, correo, token = _cliente_con_sesion(db, http_client, org_id)

    r = http_client.post(
        f"{API}/services/requests",
        json={
            "service_id": servicio.id,
            "requester_name": "Gerente",
            "requester_email": "otro-correo@example.com",
            "message": "Quiero una revision",
        },
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    assert r.json()["client_id"] == cliente.id
    assert r.json()["requester_email"] == correo, "El correo debe ser el de la sesion, no el escrito"

    visibles = http_client.get(f"{API}/services/requests", headers=_auth(token)).json()
    assert r.json()["id"] in {s["id"] for s in visibles}


def test_un_admin_no_cambia_solicitudes_de_otra_organizacion(http_client, db, admin_token):
    sufijo = uuid4().hex[:8]
    org = Organization(name=f"Ajena {sufijo}", slug=f"ajena-{sufijo}")
    db.add(org)
    db.flush()
    servicio = _servicio(db, org.id)
    solicitud = ServiceRequest(
        service_id=servicio.id,
        requester_name="Ajeno",
        requester_email="ajeno@example.com",
        status=ServiceRequestStatus.NEW,
    )
    db.add(solicitud)
    db.commit()

    r = http_client.patch(
        f"{API}/services/requests/{solicitud.id}", json={"status": "REVIEW"}, headers=_auth(admin_token)
    )
    assert r.status_code == 404, f"Cambiar una solicitud ajena devolvio {r.status_code}"
    db.expire_all()
    assert db.get(ServiceRequest, solicitud.id).status == ServiceRequestStatus.NEW
