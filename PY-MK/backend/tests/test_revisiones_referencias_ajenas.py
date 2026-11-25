"""Una revision de seguridad no puede apuntar a datos de otra organizacion.

Revision adversarial con Codex (2026-11-25): POST /security-reviews/ aceptaba
`client_id` e `integration_id` ajenos, y el PDF de la revision exportaba el nombre y
el sector de ese cliente. Lo ajeno responde 404, igual que lo inexistente.
"""

from uuid import uuid4

import pytest

from app.db.models.client import Client
from app.db.models.integration import Integration
from app.db.models.organization import Organization
from app.db.models.security_review import SecurityReview
from tests.conftest import API


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _cliente_con_integracion(db, organization_id: int, etiqueta: str) -> dict:
    sufijo = uuid4().hex[:8]
    cliente = Client(organization_id=organization_id, company_name=f"{etiqueta} {sufijo}")
    db.add(cliente)
    db.flush()
    integracion = Integration(
        organization_id=organization_id,
        client_id=cliente.id,
        connector_type="manual",
        name=f"Integracion {etiqueta} {sufijo}",
        base_url="https://ejemplo.invalid",
    )
    db.add(integracion)
    db.commit()
    return {"cliente": cliente, "integracion": integracion}


@pytest.fixture
def ajena(db):
    sufijo = uuid4().hex[:8]
    org = Organization(name=f"Ajena {sufijo}", slug=f"ajena-{sufijo}")
    db.add(org)
    db.commit()
    return _cliente_con_integracion(db, org.id, "Ajeno")


@pytest.fixture
def propia(db, seed_data):
    return _cliente_con_integracion(db, seed_data["org"].id, "Propio")


def _crear(http_client, token, cliente_id, integracion_id, **extra):
    return http_client.post(
        f"{API}/security-reviews/",
        json={"client_id": cliente_id, "integration_id": integracion_id, **extra},
        headers=_auth(token),
    )


def test_con_cliente_e_integracion_propios_se_crea(http_client, admin_token, propia):
    r = _crear(http_client, admin_token, propia["cliente"].id, propia["integracion"].id)
    assert r.status_code == 201, r.text


def test_con_cliente_ajeno_da_404_y_no_crea_nada(http_client, admin_token, ajena, propia, db):
    antes = db.query(SecurityReview).count()
    r = _crear(http_client, admin_token, ajena["cliente"].id, propia["integracion"].id)
    assert r.status_code == 404, r.text
    assert db.query(SecurityReview).count() == antes


def test_con_integracion_ajena_da_404(http_client, admin_token, ajena, propia):
    r = _crear(http_client, admin_token, propia["cliente"].id, ajena["integracion"].id)
    assert r.status_code == 404, r.text


def test_con_revisor_de_otra_organizacion_da_404(http_client, admin_token, propia, db, seed_data):
    from app.db.models.enums import RoleCode, UserStatus
    from app.db.models.user import User

    sufijo = uuid4().hex[:8]
    org = Organization(name=f"Ajena {sufijo}", slug=f"ajena-{sufijo}")
    db.add(org)
    db.flush()
    intruso = User(
        organization_id=org.id,
        role_id=seed_data["collab"].role_id,
        full_name="Intruso",
        email=f"intruso-{sufijo}@example.com",
        password_hash="x",
        role_code=RoleCode.COLLABORATOR,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(intruso)
    db.commit()
    r = _crear(
        http_client,
        admin_token,
        propia["cliente"].id,
        propia["integracion"].id,
        reviewer_user_id=intruso.id,
    )
    assert r.status_code == 404, r.text
