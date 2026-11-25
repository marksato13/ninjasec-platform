"""Un recurso de otra organizacion responde 404, nunca 403.

Auditoria de seguridad del 2026-11-25 (B8). Un 403 «not found or access denied»
confirma que el id existe en otra organizacion; la regla de AGENTS.md es 404.
"""

from uuid import uuid4

import pytest

from app.db.models.client import Client
from app.db.models.integration import Integration
from app.db.models.organization import Organization
from tests.conftest import API


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ajena(db):
    sufijo = uuid4().hex[:8]
    org = Organization(name=f"Ajena {sufijo}", slug=f"ajena-{sufijo}")
    db.add(org)
    db.flush()
    cliente = Client(organization_id=org.id, company_name=f"Cliente ajeno {sufijo}")
    db.add(cliente)
    db.flush()
    integracion = Integration(
        organization_id=org.id,
        client_id=cliente.id,
        connector_type="manual",
        name=f"Integracion ajena {sufijo}",
        base_url="https://ejemplo.invalid",
    )
    db.add(integracion)
    db.commit()
    return {"cliente": cliente, "integracion": integracion}


def test_crear_un_equipo_con_una_integracion_ajena_da_404(http_client, admin_token, ajena):
    r = http_client.post(
        f"{API}/devices/",
        json={"hostname": "infiltrado", "integration_id": ajena["integracion"].id},
        headers=_auth(admin_token),
    )
    assert r.status_code == 404, r.text


def test_crear_una_integracion_para_un_cliente_ajeno_da_404(http_client, admin_token, ajena, seed_data):
    r = http_client.post(
        f"{API}/integrations/",
        json={
            "organization_id": seed_data["org"].id,
            "client_id": ajena["cliente"].id,
            "connector_type": "manual",
            "name": "Infiltrada",
            "base_url": "https://ejemplo.invalid",
        },
        headers=_auth(admin_token),
    )
    assert r.status_code == 404, r.text


def test_listar_servicios_de_un_cliente_ajeno_responde_igual_que_uno_inexistente(http_client, admin_token, ajena):
    """El listado filtra por organizacion: un cliente ajeno y uno que no existe dan lo mismo."""
    ajeno = http_client.get(
        f"{API}/client-services/", params={"client_id": ajena["cliente"].id}, headers=_auth(admin_token)
    )
    inexistente = http_client.get(
        f"{API}/client-services/", params={"client_id": 999_999_999}, headers=_auth(admin_token)
    )
    assert (ajeno.status_code, ajeno.json()) == (inexistente.status_code, inexistente.json()) == (200, [])
