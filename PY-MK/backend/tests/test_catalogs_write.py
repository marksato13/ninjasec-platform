"""Escritura de catalogos (20-P-06 / 20-P-07).

Configuracion era un visor: crear un area exigia SQL directo. Estos tests
fijan el comportamiento de los endpoints de escritura, incluido el
aislamiento entre organizaciones y la proteccion de los catalogos globales.
"""

from app.db.models.area import Area
from app.db.models.organization import Organization
from app.db.models.project import Project
from app.db.models.project_type import ProjectType

API = "/api/v1"


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _org_ajena(db):
    org = db.query(Organization).filter(Organization.slug == "org-ajena-w").first()
    if org is None:
        org = Organization(name="Ajena Write", slug="org-ajena-w")
        db.add(org)
        db.commit()
    return org


# ------------------------------------------------------------------ crear


def test_crear_area_deriva_el_slug(http_client, admin_token):
    res = http_client.post(
        f"{API}/areas", json={"name": "Redes y Seguridad"}, headers=_auth(admin_token)
    )
    assert res.status_code == 201, res.text

    body = res.json()
    assert body["name"] == "Redes y Seguridad"
    assert body["slug"] == "redes-y-seguridad"
    assert body["is_active"] is True


def test_crear_area_normaliza_acentos_en_el_slug(http_client, admin_token):
    res = http_client.post(
        f"{API}/areas", json={"name": "Auditoría Técnica"}, headers=_auth(admin_token)
    )
    assert res.status_code == 201, res.text
    assert res.json()["slug"] == "auditoria-tecnica"


def test_el_area_creada_aparece_en_el_listado(http_client, admin_token):
    http_client.post(
        f"{API}/areas", json={"name": "Soporte Nivel 2"}, headers=_auth(admin_token)
    )
    res = http_client.get(f"{API}/areas", headers=_auth(admin_token))
    assert "Soporte Nivel 2" in {a["name"] for a in res.json()}


def test_nombre_duplicado_devuelve_409(http_client, admin_token):
    http_client.post(f"{API}/areas", json={"name": "Duplicada"}, headers=_auth(admin_token))
    res = http_client.post(
        f"{API}/areas", json={"name": "Duplicada"}, headers=_auth(admin_token)
    )
    assert res.status_code == 409, "Debe rechazarse con 409, no con un IntegrityError crudo"


def test_crear_project_type(http_client, admin_token):
    res = http_client.post(
        f"{API}/project-types",
        json={"name": "Implementación SD-WAN"},
        headers=_auth(admin_token),
    )
    assert res.status_code == 201, res.text
    assert res.json()["slug"] == "implementacion-sd-wan"


# ------------------------------------------------------------- permisos


def test_collaborator_no_puede_crear_catalogos(http_client, collaborator_token):
    res = http_client.post(
        f"{API}/areas", json={"name": "No Permitida"}, headers=_auth(collaborator_token)
    )
    assert res.status_code == 403


def test_sin_token_no_se_crea(http_client):
    res = http_client.post(f"{API}/areas", json={"name": "Anonima"})
    assert res.status_code in (401, 403)


# ---------------------------------------------------------- aislamiento


def test_no_se_puede_editar_un_area_de_otra_organizacion(db, http_client, admin_token):
    ajena = _org_ajena(db)
    area = Area(organization_id=ajena.id, name="Area De Otros", slug="area-de-otros")
    db.add(area)
    db.commit()

    res = http_client.put(
        f"{API}/areas/{area.id}", json={"name": "Secuestrada"}, headers=_auth(admin_token)
    )
    assert res.status_code == 404, "No debe confirmarse la existencia de datos ajenos"


def test_no_se_puede_editar_un_catalogo_global(db, http_client, admin_token):
    """Los catalogos globales los comparten todas las organizaciones."""
    area = Area(organization_id=None, name="Area Global W", slug="area-global-w")
    db.add(area)
    db.commit()

    res = http_client.put(
        f"{API}/areas/{area.id}", json={"name": "Apropiada"}, headers=_auth(admin_token)
    )
    assert res.status_code == 403


# ------------------------------------------------------------ desactivar


def test_desactivar_saca_del_listado(http_client, admin_token):
    creada = http_client.post(
        f"{API}/areas", json={"name": "Temporal"}, headers=_auth(admin_token)
    ).json()

    res = http_client.put(
        f"{API}/areas/{creada['id']}", json={"is_active": False}, headers=_auth(admin_token)
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    listado = http_client.get(f"{API}/areas", headers=_auth(admin_token)).json()
    assert "Temporal" not in {a["name"] for a in listado}


def test_usage_reporta_cuantos_registros_dependen(db, http_client, admin_token, seed_data):
    """20-P-07: desactivar un area usada no puede ser silencioso."""
    creada = http_client.post(
        f"{API}/areas", json={"name": "Area Con Uso"}, headers=_auth(admin_token)
    ).json()

    db.add(Project(
        organization_id=seed_data["org"].id,
        name="Proyecto Que Usa El Area",
        area_id=creada["id"],
    ))
    db.commit()

    res = http_client.get(f"{API}/areas/{creada['id']}/usage", headers=_auth(admin_token))
    assert res.status_code == 200, res.text
    assert res.json()["in_use_by"] == 1


def test_usage_de_catalogo_sin_uso_es_cero(http_client, admin_token):
    creada = http_client.post(
        f"{API}/project-types", json={"name": "Tipo Sin Uso"}, headers=_auth(admin_token)
    ).json()
    res = http_client.get(
        f"{API}/project-types/{creada['id']}/usage", headers=_auth(admin_token)
    )
    assert res.json()["in_use_by"] == 0
