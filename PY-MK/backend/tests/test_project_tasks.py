"""22-P-01: entidad ProjectTask real para el portal del colaborador."""

from __future__ import annotations

from app.core.security import hash_password
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.enums import ProjectStatus, RoleCode, UserStatus
from app.db.models.organization import Organization
from app.db.models.project import Project
from app.db.models.project_task import ProjectTask
from app.db.models.role import Role
from app.db.models.user import User

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _project(db, org_id, client_id=None, suffix="1"):
    project = Project(
        organization_id=org_id,
        client_id=client_id,
        name=f"Proyecto tareas {suffix}",
        status=ProjectStatus.ACTIVE,
    )
    db.add(project)
    db.flush()
    return project


def _collaborator(db, org_id, suffix):
    role = db.query(Role).filter(Role.code == RoleCode.COLLABORATOR.value).first()
    if role is None:
        role = Role(code=RoleCode.COLLABORATOR.value, name="Collaborator")
        db.add(role)
        db.flush()
    user = User(
        organization_id=org_id,
        role_id=role.id,
        full_name=f"Colaborador tareas {suffix}",
        email=f"colab-tareas-{suffix}@ninjasec.local",
        password_hash=hash_password("colab-password-123"),
        role_code=RoleCode.COLLABORATOR,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _collaborator_token(http_client, user):
    response = http_client.post(f"{API}/auth/login", json={
        "email": user.email,
        "password": "colab-password-123",
    })
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_admin_crea_tarea_y_colaborador_asignado_la_ve(
    db, http_client, admin_token, seed_data
):
    org_id = seed_data["org"].id
    project = _project(db, org_id, suffix="admin-crea")
    collab = _collaborator(db, org_id, "asignado")
    db.commit()

    created = http_client.post(
        f"{API}/project-tasks/",
        headers=_auth(admin_token),
        json={
            "project_id": project.id,
            "assigned_user_id": collab.id,
            "title": "Revisar firewall perimetral",
            "description": "Ajustar reglas tras el hallazgo crítico",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "pending"
    assert body["project_name"] == project.name
    assert body["assigned_user_name"] == collab.full_name

    own_token = _collaborator_token(http_client, collab)
    listed = http_client.get(f"{API}/project-tasks/", headers=_auth(own_token))
    assert listed.status_code == 200, listed.text
    assert any(t["id"] == body["id"] for t in listed.json())


def test_colaborador_no_ve_tareas_de_otro_colaborador(
    db, http_client, admin_token, seed_data
):
    org_id = seed_data["org"].id
    project = _project(db, org_id, suffix="aislamiento")
    owner = _collaborator(db, org_id, "dueno")
    other = _collaborator(db, org_id, "ajeno")
    db.commit()

    task = ProjectTask(
        organization_id=org_id,
        project_id=project.id,
        assigned_user_id=owner.id,
        title="Tarea privada",
    )
    db.add(task)
    db.commit()

    other_token = _collaborator_token(http_client, other)
    listed = http_client.get(f"{API}/project-tasks/", headers=_auth(other_token))
    assert listed.status_code == 200, listed.text
    assert all(t["id"] != task.id for t in listed.json())


def test_tarea_de_otra_organizacion_no_es_visible(db, http_client, admin_token, seed_data):
    other_org = Organization(name="Tenant tareas ajeno", slug="tenant-tareas-ajeno")
    db.add(other_org)
    db.flush()
    other_project = _project(db, other_org.id, suffix="ajeno")
    other_collab = _collaborator(db, other_org.id, "otra-org")
    db.commit()

    task = ProjectTask(
        organization_id=other_org.id,
        project_id=other_project.id,
        assigned_user_id=other_collab.id,
        title="Tarea de otro tenant",
    )
    db.add(task)
    db.commit()

    listed = http_client.get(f"{API}/project-tasks/", headers=_auth(admin_token))
    assert listed.status_code == 200, listed.text
    assert all(t["id"] != task.id for t in listed.json())


def test_cliente_ve_tareas_de_sus_proyectos_no_de_otros(
    db, http_client, admin_token, seed_data
):
    org_id = seed_data["org"].id
    client_a = Client(organization_id=org_id, company_name="Cliente A tareas")
    client_b = Client(organization_id=org_id, company_name="Cliente B tareas")
    db.add_all([client_a, client_b])
    db.flush()

    project_a = _project(db, org_id, client_id=client_a.id, suffix="cliente-a")
    project_b = _project(db, org_id, client_id=client_b.id, suffix="cliente-b")
    collab = _collaborator(db, org_id, "para-clientes")
    db.commit()

    task_a = ProjectTask(
        organization_id=org_id, project_id=project_a.id,
        assigned_user_id=collab.id, title="Tarea de A",
    )
    task_b = ProjectTask(
        organization_id=org_id, project_id=project_b.id,
        assigned_user_id=collab.id, title="Tarea de B",
    )
    db.add_all([task_a, task_b])
    db.commit()

    role = db.query(Role).filter(Role.code == RoleCode.CLIENT.value).first()
    if role is None:
        role = Role(code=RoleCode.CLIENT.value, name="Client")
        db.add(role)
        db.flush()
    client_user = User(
        organization_id=org_id,
        role_id=role.id,
        full_name="Portal cliente A tareas",
        email="portal-cliente-a-tareas@ninjasec.local",
        password_hash=hash_password("client-password-123"),
        role_code=RoleCode.CLIENT,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(client_user)
    db.flush()
    db.add(ClientProfile(client_id=client_a.id, user_id=client_user.id))
    db.commit()

    login = http_client.post(f"{API}/auth/login", json={
        "email": client_user.email, "password": "client-password-123",
    })
    assert login.status_code == 200, login.text
    client_token = login.json()["access_token"]

    listed = http_client.get(f"{API}/project-tasks/", headers=_auth(client_token))
    assert listed.status_code == 200, listed.text
    ids = {t["id"] for t in listed.json()}
    assert task_a.id in ids
    assert task_b.id not in ids


def test_admin_actualiza_estado_y_reasignacion(db, http_client, admin_token, seed_data):
    org_id = seed_data["org"].id
    project = _project(db, org_id, suffix="update")
    collab = _collaborator(db, org_id, "update-inicial")
    other_collab = _collaborator(db, org_id, "update-nuevo")
    db.commit()

    task = ProjectTask(
        organization_id=org_id, project_id=project.id,
        assigned_user_id=collab.id, title="Tarea a actualizar",
    )
    db.add(task)
    db.commit()

    updated = http_client.put(
        f"{API}/project-tasks/{task.id}",
        headers=_auth(admin_token),
        json={"status": "done", "assigned_user_id": other_collab.id},
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["status"] == "done"
    assert body["assigned_user_id"] == other_collab.id


def test_colaborador_no_puede_crear_ni_actualizar_tareas(
    db, http_client, admin_token, collaborator_token, seed_data
):
    org_id = seed_data["org"].id
    project = _project(db, org_id, suffix="sin-permiso")
    collab = _collaborator(db, org_id, "sin-permiso")
    db.commit()

    denied_create = http_client.post(
        f"{API}/project-tasks/",
        headers=_auth(collaborator_token),
        json={"project_id": project.id, "assigned_user_id": collab.id, "title": "No autorizado"},
    )
    assert denied_create.status_code == 403
