"""26-P1: CRUD de auditorías formales + regla de independencia + export PDF."""

from __future__ import annotations

from uuid import uuid4

from app.core.security import hash_password
from app.db.models.client import Client
from app.db.models.enums import ProjectStatus, RoleCode, UserStatus
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.role import Role
from app.db.models.user import User

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _client(db, org_id, suffix):
    client = Client(organization_id=org_id, company_name=f"Cliente auditoria {suffix}")
    db.add(client)
    db.commit()
    return client


def _collaborator(db, org_id, suffix):
    role = db.query(Role).filter(Role.code == RoleCode.COLLABORATOR.value).first()
    if role is None:
        role = Role(code=RoleCode.COLLABORATOR.value, name="Collaborator")
        db.add(role)
        db.flush()
    identifier = uuid4().hex[:8]
    user = User(
        organization_id=org_id,
        role_id=role.id,
        full_name=f"Auditor {suffix}",
        email=f"auditor-{suffix}-{identifier}@ninjasec.local",
        password_hash=hash_password("unused"),
        role_code=RoleCode.COLLABORATOR,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def _make_responsible(db, org_id, user, client):
    """Vuelve a `user` responsable operativo de `client` vía ProjectMember."""
    project = Project(
        organization_id=org_id, client_id=client.id,
        name=f"Proyecto de {client.company_name}", status=ProjectStatus.ACTIVE,
    )
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=user.id))
    db.commit()


def test_crear_auditoria_genera_code_correlativo(db, http_client, admin_token, seed_data):
    org_id = seed_data["org"].id
    client = _client(db, org_id, "correlativo")
    auditor = _collaborator(db, org_id, "correlativo")

    first = http_client.post(f"{API}/audits/", headers=_auth(admin_token), json={
        "client_id": client.id, "title": "Auditoría anual",
        "framework": "cobit_2019", "audit_type": "internal",
        "lead_auditor_id": auditor.id,
    })
    assert first.status_code == 201, first.text
    code_a = first.json()["code"]

    second = http_client.post(f"{API}/audits/", headers=_auth(admin_token), json={
        "client_id": client.id, "title": "Auditoría de seguimiento",
        "framework": "iso_19011", "audit_type": "follow_up",
        "lead_auditor_id": auditor.id,
    })
    assert second.status_code == 201, second.text
    code_b = second.json()["code"]

    assert code_a != code_b
    assert code_a.startswith("AUD-")
    num_a = int(code_a.rsplit("-", 1)[1])
    num_b = int(code_b.rsplit("-", 1)[1])
    assert num_b == num_a + 1


def test_auditor_responsable_operativo_es_bloqueado(db, http_client, admin_token, seed_data):
    org_id = seed_data["org"].id
    client = _client(db, org_id, "independencia")
    auditor = _collaborator(db, org_id, "independencia")
    _make_responsible(db, org_id, auditor, client)

    response = http_client.post(f"{API}/audits/", headers=_auth(admin_token), json={
        "client_id": client.id, "title": "Auditoría con conflicto",
        "framework": "cobit_2019", "audit_type": "internal",
        "lead_auditor_id": auditor.id,
    })
    assert response.status_code == 422
    assert "independencia" in response.text.lower()


def test_auditor_sin_conflicto_puede_ser_asignado(db, http_client, admin_token, seed_data):
    org_id = seed_data["org"].id
    client = _client(db, org_id, "sin-conflicto")
    other_client = _client(db, org_id, "otro-cliente")
    auditor = _collaborator(db, org_id, "sin-conflicto")
    # Responsable de OTRO cliente, no del auditado -- no debe bloquear.
    _make_responsible(db, org_id, auditor, other_client)

    response = http_client.post(f"{API}/audits/", headers=_auth(admin_token), json={
        "client_id": client.id, "title": "Auditoría sin conflicto",
        "framework": "cobit_2019", "audit_type": "internal",
        "lead_auditor_id": auditor.id,
    })
    assert response.status_code == 201, response.text


def test_exportar_plan_a_pdf_incluye_secciones_normativas(db, http_client, admin_token, seed_data):
    org_id = seed_data["org"].id
    client = _client(db, org_id, "pdf")
    auditor = _collaborator(db, org_id, "pdf")

    created = http_client.post(f"{API}/audits/", headers=_auth(admin_token), json={
        "client_id": client.id, "title": "Auditoría exportable",
        "objective": "Verificar controles de acceso",
        "scope": "Sistemas de información en producción",
        "framework": "cobit_2019", "audit_type": "internal",
        "lead_auditor_id": auditor.id,
    })
    assert created.status_code == 201, created.text
    audit_id = created.json()["id"]

    pdf = http_client.get(f"{API}/audits/{audit_id}/plan-pdf", headers=_auth(admin_token))
    assert pdf.status_code == 200, pdf.text
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content[:4] == b"%PDF"
    assert len(pdf.content) > 500


def test_cliente_de_otra_organizacion_no_es_visible(db, http_client, admin_token, seed_data):
    from app.db.models.organization import Organization

    other_org = Organization(name="Tenant auditorias ajeno", slug="tenant-auditorias-ajeno")
    db.add(other_org)
    db.flush()
    other_client = _client(db, other_org.id, "otra-org")
    other_auditor = _collaborator(db, other_org.id, "otra-org")

    response = http_client.post(f"{API}/audits/", headers=_auth(admin_token), json={
        "client_id": other_client.id, "title": "No debería crearse",
        "framework": "cobit_2019", "audit_type": "internal",
        "lead_auditor_id": other_auditor.id,
    })
    assert response.status_code == 404


def test_colaborador_consulta_pero_no_crea(db, http_client, collaborator_token, seed_data):
    org_id = seed_data["org"].id
    client = _client(db, org_id, "colaborador")
    auditor = _collaborator(db, org_id, "colaborador")

    listed = http_client.get(f"{API}/audits/", headers=_auth(collaborator_token))
    assert listed.status_code == 200

    denied = http_client.post(f"{API}/audits/", headers=_auth(collaborator_token), json={
        "client_id": client.id, "title": "No autorizado",
        "framework": "cobit_2019", "audit_type": "internal",
        "lead_auditor_id": auditor.id,
    })
    assert denied.status_code == 403
