"""Flujo completo de catálogos de proyectos (20-P-01, 20-P-02 y 20-P-04).

Estas pruebas recorren las mismas operaciones que realiza un administrador
desde Configuración y al crear un proyecto. La preparación de un cliente y un
servicio representa datos preexistentes; el administrador sólo usa la API.
"""

from app.db.models.client import Client
from app.db.models.project import Project
from app.db.models.service import Service


API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _crear_dependencias(db, seed_data, area_id, project_type_id):
    """Crea el contexto existente que usará el proyecto del flujo."""
    client = Client(
        organization_id=seed_data["org"].id,
        company_name="Cliente de catálogo E2E",
    )
    service = Service(
        organization_id=seed_data["org"].id,
        area_id=area_id,
        project_type_id=project_type_id,
        title="Servicio de catálogo E2E",
        slug="servicio-catalogo-e2e",
    )
    db.add_all([client, service])
    db.commit()
    return client, service


def _crear_proyecto(http_client, token, organization_id, client_id, type_id, service_id):
    response = http_client.post(
        f"{API}/projects/",
        headers=_auth(token),
        json={
            "organization_id": organization_id,
            "client_id": client_id,
            "project_type_id": type_id,
            "service_id": service_id,
            "name": "Proyecto histórico de catálogo",
            "status": "planning",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_admin_gestiona_catalogos_y_los_retiros_no_rompen_proyectos_existentes(
    db, http_client, admin_token, seed_data
):
    """El flujo de pantalla no requiere SQL y protege referencias históricas."""
    headers = _auth(admin_token)

    # Alta y edición desde Configuración.
    area = http_client.post(
        f"{API}/areas", headers=headers, json={"name": "Área E2E inicial"}
    )
    project_type = http_client.post(
        f"{API}/project-types", headers=headers, json={"name": "Tipo E2E inicial"}
    )
    assert area.status_code == project_type.status_code == 201

    area = http_client.put(
        f"{API}/areas/{area.json()['id']}",
        headers=headers,
        json={"name": "Área E2E editada"},
    )
    project_type = http_client.put(
        f"{API}/project-types/{project_type.json()['id']}",
        headers=headers,
        json={"name": "Tipo E2E editado"},
    )
    assert area.status_code == project_type.status_code == 200
    area = area.json()
    project_type = project_type.json()
    assert area["name"] == "Área E2E editada"
    assert project_type["name"] == "Tipo E2E editado"

    client, service = _crear_dependencias(
        db, seed_data, area["id"], project_type["id"]
    )
    project = _crear_proyecto(
        http_client,
        admin_token,
        seed_data["org"].id,
        client.id,
        project_type["id"],
        service.id,
    )

    # La advertencia enumera dependencias y no permite desactivar sin confirmar.
    for path, item in (("areas", area), ("project-types", project_type)):
        usage = http_client.get(f"{API}/{path}/{item['id']}/usage", headers=headers)
        assert usage.status_code == 200, usage.text
        assert usage.json()["in_use_by"] == 2  # servicio + proyecto

        unconfirmed = http_client.put(
            f"{API}/{path}/{item['id']}",
            headers=headers,
            json={"is_active": False},
        )
        assert unconfirmed.status_code == 409
        assert unconfirmed.json()["detail"]["in_use_by"] == 2

        deactivated = http_client.put(
            f"{API}/{path}/{item['id']}",
            headers=headers,
            json={"is_active": False, "confirm_deactivation": True},
        )
        assert deactivated.status_code == 200, deactivated.text
        assert deactivated.json()["is_active"] is False

    # Los selectores de un proyecto nuevo sólo consumen estos listados activos.
    visible_areas = http_client.get(f"{API}/areas", headers=headers).json()
    visible_types = http_client.get(f"{API}/project-types", headers=headers).json()
    assert area["id"] not in {item["id"] for item in visible_areas}
    assert project_type["id"] not in {item["id"] for item in visible_types}

    # El proyecto creado antes del retiro conserva sus referencias y es editable.
    existing = http_client.get(f"{API}/projects/{project['id']}", headers=headers)
    assert existing.status_code == 200, existing.text
    assert existing.json()["area_id"] == area["id"]
    assert existing.json()["project_type_id"] == project_type["id"]

    updated = http_client.put(
        f"{API}/projects/{project['id']}",
        headers=headers,
        json={"name": "Proyecto histórico actualizado"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Proyecto histórico actualizado"
    assert db.get(Project, project["id"]).area_id == area["id"]
